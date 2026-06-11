from flask import Blueprint, render_template, url_for, session
from pathlib import Path
from src.utils.nav_helper import get_nav_data
from src.utils.auth_utils import require_login
from src.models.ModeloUsuario import ModeloUsuario

# Blueprint para manejar las rutas
template_dir = Path(__file__).parent.parent / 'templates' / 'profile'
user = Blueprint('user_blueprint', __name__, url_prefix='/usuario', template_folder=str(template_dir))

def links_sidebar():
    items = [
        {"name": "Perfil Principal", "url": url_for('user_blueprint.profile'), "icon":"fa-regular fa-circle-user"},
        {"name": "Carrito de Compras", "url": url_for('user_blueprint.user_cart'), "icon":"fa-solid fa-cart-shopping"},
        {"name": "Pedidos Realizados", "url": url_for('user_blueprint.user_history'), "icon":"fa-solid fa-clock-rotate-left"}
    ]
    return items

@user.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja',mensaje=error, categorias=get_nav_data())

@user.route('/')
@require_login
def profile():
    user = ModeloUsuario.get_by_id(session['user_id'])
    items = links_sidebar()
    return render_template('profile.html', items=items, user=user)
@user.route('/carrito')
@require_login
def user_cart():
    items = links_sidebar()
    return render_template('profile-cart.html', items=items)
@user.route('/historial')
@require_login
def user_history():
    items = links_sidebar()
    return render_template('profile-pedidos.html', items=items)