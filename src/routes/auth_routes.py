from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from pathlib import Path
from src.forms.auth_forms import LoginForm, RegisterForm
from src.models.ModeloUsuario import ModeloUsuario
from src.utils.nav_helper import get_nav_data

# Blueprint para manejar las rutas
template_dir = Path(__file__).parent.parent / 'templates' / 'auth'
auth = Blueprint('auth_blueprint', __name__, url_prefix='/auth', template_folder=str(template_dir))

@auth.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja', mensaje=error, categorias=get_nav_data())

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_url = request.args.get('next')

    if form.validate_on_submit():
        user = ModeloUsuario.get_by_email(form.email.data)
        if user and ModeloUsuario.verify_password(form.password.data, user['contrasena']):
            session.clear()
            session['user_id'] = user['id_usuario']
            session['user_nombre'] = user['nombre']
            session['user_email'] = user['email']

            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(next_url or url_for('user_blueprint.profile'))

        flash('Correo electrónico o contraseña incorrectos.', 'danger')

    return render_template('login.jinja', form=form, categorias=get_nav_data())

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = ModeloUsuario.get_by_email(form.email.data)
        if existing_user:
            flash('Ya existe una cuenta con ese correo electrónico.', 'danger')
        else:
            success = ModeloUsuario.create(
                nombre=form.nombre.data,
                email=form.email.data,
                password=form.password.data,
                direccion=form.direccion.data,
                celular=form.celular.data,
                telefono=form.telefono.data,
            )
            if success:
                flash('Registro completo. Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('auth_blueprint.login'))
            flash('Ocurrió un error al crear la cuenta. Intenta nuevamente.', 'danger')

    return render_template('register.jinja', form=form, categorias=get_nav_data())

@auth.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth_blueprint.login'))
