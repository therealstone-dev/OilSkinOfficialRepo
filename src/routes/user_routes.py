from flask import Blueprint, render_template
from pathlib import Path
from src.utils.nav_helper import get_nav_data

# Blueprint para manejar las rutas
template_dir = Path(__file__).parent.parent / 'templates' / 'profile'
user = Blueprint('user_blueprint', __name__, url_prefix='/usuario', template_folder=str(template_dir))

@user.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja',mensaje=error, categorias=get_nav_data())

@user.route('/perfil/<string:username>')
def profile(username):
    return render_template('profile.html', user=username)
@user.route('/perfil/carrito')
def user_cart():
    return render_template('profile-cart.html')
@user.route('/perfil/historial')
def user_history():
    return render_template('profile-pedidos.html')