from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from pathlib import Path
from src.utils.nav_helper import get_nav_data
from src.forms.auth_forms import LoginForm, RegisterForm
from src.models.ModeloUsuario import ModeloUsuario

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
            # Guardar datos en sesión
            session['user_id'] = user.get('id_usuario') if isinstance(user, dict) else user[0]
            session['user_name'] = user.get('nombre') if isinstance(user, dict) else user[1]
            flash('Inicio de sesión exitoso', 'success')
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

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('main_blueprint.index'))