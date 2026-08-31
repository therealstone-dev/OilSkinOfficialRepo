from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from pathlib import Path
from src.utils.nav_helper import get_nav_data
from src.forms.auth_forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from src.models.ModeloUsuario import ModeloUsuario
from src.utils.token_service import generate_reset_token, verify_reset_token
from src.services.email_service import send_password_reset_email

# Blueprint para manejar las rutas
template_dir = Path(__file__).parent.parent / 'templates' / 'auth'
auth = Blueprint('auth_blueprint', __name__, url_prefix='/auth', template_folder=str(template_dir))

@auth.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja',mensaje=error, categorias=get_nav_data())

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        ok, user = ModeloUsuario.verify_password(email, password)
        if ok:
            # Verificar si el usuario está restringido
            is_active = user.get('activo', 1) if isinstance(user, dict) else 1
            if not is_active:
                flash('Tu cuenta ha sido restringida por un administrador. Contacta soporte.', 'danger')
                return render_template('login.jinja', categorias=get_nav_data(), form=form)

            # Guardar datos en sesión
            session.permanent = True
            session['user_id'] = user.get('id_usuario') if isinstance(user, dict) else user[0]
            session['user_name'] = user.get('nombre') if isinstance(user, dict) else user[1]
            session['user_email'] = user.get('email') if isinstance(user, dict) else user[6]
            session['id_rol'] = user.get('id_rol') if isinstance(user, dict) else (user[8] if len(user) > 8 else 1)
            flash('Inicio de sesión exitoso', 'success')
            if session['id_rol'] == 2:
                return redirect(url_for('admin_blueprint.dashboard'))
            return redirect(url_for('user_blueprint.profile'))

        else:
            flash('Credenciales inválidas', 'danger')
    return render_template('login.jinja', categorias=get_nav_data(), form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        email = form.email.data
        direccion = form.direccion.data
        celular = form.celular.data
        telefono = form.telefono.data
        password = form.password.data
        # Crear usuario
        user_id = ModeloUsuario.create(nombre, email, password, direccion, celular, telefono)
        if user_id:
            flash('Cuenta creada correctamente. Por favor inicia sesión.', 'success')
            return redirect(url_for('auth_blueprint.login'))
        else:
            flash('Error al crear la cuenta. Intenta nuevamente.', 'danger')
    return render_template('register.jinja', categorias=get_nav_data(), form=form)

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    reset_link = None
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = ModeloUsuario.get_by_email(email)
        if user:
            user_id = user.get('id_usuario') if isinstance(user, dict) else user[0]
            user_name = user.get('nombre') if isinstance(user, dict) else (user[1] if len(user) > 1 else 'Cliente')
            token = generate_reset_token(email=email, user_id=user_id)
            reset_link = url_for('auth_blueprint.reset_password', token=token, _external=True)
            
            # Intento de envío de correo real vía SMTP
            sent, msg = send_password_reset_email(to_email=email, reset_url=reset_link, user_name=user_name)
            if sent:
                flash(f'¡Correo enviado con éxito a {email}! Revisa tu bandeja de entrada o carpeta de spam.', 'success')
                reset_link = None  # No es necesario mostrar el link en pantalla si se envió con éxito
            else:
                flash(f'{msg}', 'warning')
        else:
            flash('No se encontró ninguna cuenta registrada con ese correo electrónico.', 'danger')
    return render_template('forgot_password.jinja', categorias=get_nav_data(), form=form, reset_link=reset_link)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    payload = verify_reset_token(token, max_age=3600)
    if not payload:
        flash('El enlace de recuperación es inválido o ha expirado (validez de 1 hora). Por favor solicita uno nuevo.', 'danger')
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
    return render_template('reset_password.jinja', categorias=get_nav_data(), form=form, token=token, email=user_email_display)

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('main_blueprint.index'))