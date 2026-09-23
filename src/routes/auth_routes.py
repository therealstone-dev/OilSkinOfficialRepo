import secrets
import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from pathlib import Path
from src.utils.nav_helper import get_nav_data
from src.forms.auth_forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm, VerifyCodeForm
from src.models.ModeloUsuario import ModeloUsuario
from src.utils.token_service import generate_reset_token, verify_reset_token
from src.services.email_service import send_password_reset_email, send_password_reset_otp
from src.services.oauth_service import is_google_oauth_configured, get_google_auth_url, exchange_code_for_user_info

# Blueprint para manejar las rutas
template_dir = Path(__file__).parent.parent / 'templates' / 'auth'
auth = Blueprint('auth_blueprint', __name__, url_prefix='/auth', template_folder=str(template_dir))

@auth.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja', mensaje=error, categorias=get_nav_data())

# ==================== RUTAS DE INICIO Y REGISTRO ====================

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    google_available = is_google_oauth_configured()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        ok, user = ModeloUsuario.verify_password(email, password)
        if ok:
            # Verificar si el usuario está restringido
            is_active = user.get('activo', 1) if isinstance(user, dict) else 1
            if not is_active:
                flash('Tu cuenta ha sido restringida por un administrador. Contacta a soporte.', 'danger')
                return render_template('login.jinja', categorias=get_nav_data(), form=form, google_available=google_available)

            # Guardar datos en sesión
            session.permanent = True
            session['user_id'] = user.get('id_usuario') if isinstance(user, dict) else user[0]
            session['user_name'] = user.get('nombre') if isinstance(user, dict) else user[1]
            session['user_email'] = user.get('email') if isinstance(user, dict) else user[6]
            session['id_rol'] = user.get('id_rol') if isinstance(user, dict) else (user[8] if len(user) > 8 else 1)
            session['auth_provider'] = user.get('auth_provider', 'local') if isinstance(user, dict) else 'local'
            flash('Inicio de sesión exitoso', 'success')
            if session['id_rol'] == 2:
                return redirect(url_for('admin_blueprint.dashboard'))
            return redirect(url_for('user_blueprint.profile'))

        else:
            flash('Credenciales inválidas. Verifica tu correo y contraseña.', 'danger')
    return render_template('login.jinja', categorias=get_nav_data(), form=form, google_available=google_available)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    google_available = is_google_oauth_configured()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        email = form.email.data.strip().lower()
        direccion = form.direccion.data.strip()
        celular = form.celular.data.strip()
        telefono = form.telefono.data.strip() if form.telefono.data else None
        password = form.password.data
        # Crear usuario
        user_id = ModeloUsuario.create(nombre, email, password, direccion, celular, telefono)
        if user_id:
            flash('Cuenta creada correctamente. Por favor inicia sesión.', 'success')
            return redirect(url_for('auth_blueprint.login'))
        else:
            flash('Error al crear la cuenta. Intenta nuevamente.', 'danger')
    return render_template('register.jinja', categorias=get_nav_data(), form=form, google_available=google_available)

# ==================== RUTAS DE GOOGLE OAUTH 2.0 ====================

@auth.route('/google')
def google_login():
    """Inicia el flujo de autenticación con Google redirigiendo a la pantalla de consentimiento."""
    if not is_google_oauth_configured():
        flash('El inicio de sesión con Google aún no ha sido configurado por el administrador.', 'warning')
        return redirect(url_for('auth_blueprint.login'))

    state = secrets.token_urlsafe(24)
    session['google_oauth_state'] = state
    redirect_uri = url_for('auth_blueprint.google_callback', _external=True)
    auth_url = get_google_auth_url(redirect_uri=redirect_uri, state=state)
    return redirect(auth_url)

@auth.route('/google/callback')
def google_callback():
    """Recibe la respuesta de Google tras el consentimiento del usuario."""
    error = request.args.get('error')
    if error:
        flash(f'Autenticación de Google cancelada o denegada: {error}', 'warning')
        return redirect(url_for('auth_blueprint.login'))

    incoming_state = request.args.get('state')
    saved_state = session.pop('google_oauth_state', None)
    if not incoming_state or incoming_state != saved_state:
        flash('Error de seguridad (CSRF) en la respuesta de Google. Por favor intenta de nuevo.', 'danger')
        return redirect(url_for('auth_blueprint.login'))

    code = request.args.get('code')
    if not code:
        flash('No se recibió el código de autorización de Google.', 'danger')
        return redirect(url_for('auth_blueprint.login'))

    redirect_uri = url_for('auth_blueprint.google_callback', _external=True)
    exito, user_info = exchange_code_for_user_info(code, redirect_uri)
    if not exito or not isinstance(user_info, dict):
        flash(f'Error al conectar con Google: {user_info}', 'danger')
        return redirect(url_for('auth_blueprint.login'))

    google_id = user_info.get('google_id')
    email = user_info.get('email')
    nombre = user_info.get('name') or 'Usuario Google'
    foto = user_info.get('picture')

    # 1. Buscar si ya existe por google_id
    user = ModeloUsuario.get_by_google_id(google_id)

    # 2. Si no existe por google_id, buscar por correo para vincular
    if not user:
        user = ModeloUsuario.get_by_email(email)
        if user:
            id_usuario = user.get('id_usuario') if isinstance(user, dict) else user[0]
            ModeloUsuario.link_google_account(id_usuario, google_id, foto)
            user = ModeloUsuario.get_by_id(id_usuario)
        else:
            # 3. Crear nuevo usuario autenticado con Google
            new_id = ModeloUsuario.create_google_user(nombre, email, google_id, foto)
            if not new_id:
                flash('No se pudo registrar la cuenta con Google. Intenta nuevamente.', 'danger')
                return redirect(url_for('auth_blueprint.login'))
            user = ModeloUsuario.get_by_id(new_id)

    # Verificar si el usuario está restringido
    is_active = user.get('activo', 1) if isinstance(user, dict) else 1
    if not is_active:
        flash('Tu cuenta ha sido restringida por un administrador. Contacta a soporte.', 'danger')
        return redirect(url_for('auth_blueprint.login'))

    # Iniciar sesión
    session.permanent = True
    session['user_id'] = user.get('id_usuario') if isinstance(user, dict) else user[0]
    session['user_name'] = user.get('nombre') if isinstance(user, dict) else user[1]
    session['user_email'] = user.get('email') if isinstance(user, dict) else user[6]
    session['id_rol'] = user.get('id_rol') if isinstance(user, dict) else (user[8] if len(user) > 8 else 1)
    session['auth_provider'] = 'google'
    session['user_avatar'] = user.get('foto_perfil') if isinstance(user, dict) else None

    flash(f'¡Bienvenido(a), {session["user_name"]}! Has iniciado sesión con Google.', 'success')
    if session['id_rol'] == 2:
        return redirect(url_for('admin_blueprint.dashboard'))
    return redirect(url_for('user_blueprint.profile'))

# ==================== RECUPERACIÓN CON CÓDIGOS OTP ====================

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = ModeloUsuario.get_by_email(email)
        if user:
            id_usuario = user.get('id_usuario') if isinstance(user, dict) else user[0]
            user_name = user.get('nombre') if isinstance(user, dict) else (user[1] if len(user) > 1 else 'Cliente')

            # Generar código OTP criptográfico de 6 dígitos
            otp_code = f"{secrets.randbelow(1000000):06d}"
            otp_hash = hashlib.sha256(otp_code.encode('utf-8')).hexdigest()

            # Guardar en base de datos con 15 minutos de validez
            ModeloUsuario.guardar_codigo_recuperacion(id_usuario, otp_hash, minutos_validez=15)

            # Envío de correo electrónico transaccional
            sent, msg = send_password_reset_otp(to_email=email, otp_code=otp_code, user_name=user_name)

            # Guardar correo temporal en sesión para la pantalla de verificación
            session['otp_email'] = email
            session['otp_user_name'] = user_name

            if sent:
                flash(f'¡Código de verificación enviado a {email}! Revisa tu bandeja de entrada o spam.', 'success')
            else:
                flash(f'{msg} (Para pruebas locales: código generado: {otp_code})', 'warning')

            return redirect(url_for('auth_blueprint.verify_code'))
        else:
            flash('No se encontró ninguna cuenta registrada con ese correo electrónico.', 'danger')
    return render_template('forgot_password.jinja', categorias=get_nav_data(), form=form)

@auth.route('/verify-code', methods=['GET', 'POST'])
def verify_code():
    """Pantalla interactiva para validar el código numérico de 6 dígitos."""
    email = session.get('otp_email')
    if not email:
        flash('Por favor solicita un código de recuperación antes de verificar.', 'warning')
        return redirect(url_for('auth_blueprint.forgot_password'))

    form = VerifyCodeForm()
    if form.validate_on_submit():
        codigo = form.codigo.data.strip()
        ok, msg, user = ModeloUsuario.verificar_codigo_recuperacion(email, codigo)
        if ok and user:
            id_usuario = user.get('id_usuario') if isinstance(user, dict) else user[0]
            session.pop('otp_email', None)
            session['reset_authorized_user_id'] = id_usuario
            session['reset_authorized_email'] = email
            flash('¡Código verificado exitosamente! Ahora puedes definir tu nueva contraseña.', 'success')
            return redirect(url_for('auth_blueprint.reset_password'))
        else:
            flash(msg, 'danger')

    return render_template('verify_code.jinja', categorias=get_nav_data(), form=form, email=email)

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Permite establecer la nueva contraseña tras verificar el código OTP."""
    target_user_id = session.get('reset_authorized_user_id')
    target_email = session.get('reset_authorized_email')

    if not target_user_id:
        flash('Acceso no autorizado o tiempo expirado. Solicita un nuevo código de recuperación.', 'danger')
        return redirect(url_for('auth_blueprint.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        new_password = form.password.data
        ok, msg = ModeloUsuario.update_password(target_user_id, new_password)
        if ok:
            session.pop('reset_authorized_user_id', None)
            session.pop('reset_authorized_email', None)
            flash('¡Tu contraseña ha sido restablecida exitosamente! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth_blueprint.login'))
        else:
            flash(f'Error al restablecer la contraseña: {msg}', 'danger')

    return render_template('reset_password.jinja', categorias=get_nav_data(), form=form, email=target_email)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    """Soporte retrocompatible para enlaces de recuperación con token itsdangerous."""
    payload = verify_reset_token(token, max_age=3600)
    if not payload:
        flash('El enlace de recuperación es inválido o ha expirado. Por favor solicita un nuevo código.', 'danger')
        return redirect(url_for('auth_blueprint.forgot_password'))

    email = payload.get('email')
    user_id = payload.get('user_id')
    user = ModeloUsuario.get_by_id(user_id) if user_id else ModeloUsuario.get_by_email(email)

    if not user:
        flash('El usuario asociado a este enlace ya no existe.', 'danger')
        return redirect(url_for('auth_blueprint.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        new_password = form.password.data
        target_user_id = user.get('id_usuario') if isinstance(user, dict) else user[0]
        ok, msg = ModeloUsuario.update_password(target_user_id, new_password)
        if ok:
            flash('¡Tu contraseña ha sido restablecida exitosamente! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth_blueprint.login'))
        else:
            flash(f'Error al restablecer la contraseña: {msg}', 'danger')

    user_email_display = user.get('email') if isinstance(user, dict) else user[6]
    return render_template('reset_password.jinja', categorias=get_nav_data(), form=form, email=user_email_display)

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('id_rol', None)
    session.pop('auth_provider', None)
    session.pop('user_avatar', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('main_blueprint.index'))
