from flask import Blueprint, render_template
from pathlib import Path
from src.utils.nav_helper import get_nav_data

# Blueprint para manejar las rutas
template_dir = Path(__file__).parent.parent / 'templates' / 'auth'
auth = Blueprint('auth_blueprint', __name__, url_prefix='/auth', template_folder=str(template_dir))

@auth.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja',mensaje=error, categorias=get_nav_data())

@auth.route('/login')
def login():
    return render_template('login.jinja', categorias=get_nav_data())
@auth.route('/register')
def register():
    return render_template('register.jinja', categorias=get_nav_data())