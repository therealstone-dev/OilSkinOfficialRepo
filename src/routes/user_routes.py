from flask import Blueprint, render_template, url_for, session, request, redirect, flash
from pathlib import Path
from src.utils.nav_helper import get_nav_data
from src.utils.auth_utils import require_login
from src.models.ModeloUsuario import ModeloUsuario
from src.models.ModeloCarrito import ModeloCarrito
from src.models.ModeloPedido import ModeloPedido

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
    return render_template('error_page.jinja', mensaje=error, categorias=get_nav_data())

@user.route('/')
@require_login
def profile():
    user_data = ModeloUsuario.get_by_id(session['user_id'])
    items = links_sidebar()
    return render_template('profile.html', items=items, user=user_data)

@user.route('/actualizar', methods=['POST'])
@require_login
def update_profile():
    user_id = session['user_id']
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    direccion = request.form.get('direccion', '').strip()
    celular = request.form.get('celular', '').strip()
    telefono = request.form.get('telefono', '').strip() or None

    if not nombre or not email or not direccion or not celular:
        flash('Por favor completa todos los campos obligatorios.', 'danger')
        return redirect(url_for('user_blueprint.profile'))

    exito, mensaje = ModeloUsuario.update_profile(
        id_usuario=user_id,
        nombre=nombre,
        email=email,
        direccion=direccion,
        celular=celular,
        telefono=telefono
    )

    if exito:
        session['user_name'] = nombre
        session['user_email'] = email
        flash(mensaje, 'success')
    else:
        flash(mensaje, 'danger')

    return redirect(url_for('user_blueprint.profile'))

@user.route('/carrito')
@require_login
def user_cart():
    user_data = ModeloUsuario.get_by_id(session['user_id'])
    items = links_sidebar()
    carrito = ModeloCarrito.obtener_carrito()
    total_items = ModeloCarrito.total_items()
    total_precio = ModeloCarrito.total_precio()
    return render_template(
        'profile-cart.html',
        items=items,
        user=user_data,
        carrito=carrito,
        total_items=total_items,
        total_precio=total_precio
    )

@user.route('/carrito/actualizar', methods=['POST'])
@require_login
def update_cart_item():
    producto_id = request.form.get('producto_id', type=int)
    cantidad = request.form.get('cantidad', type=int)

    if producto_id and cantidad is not None:
        actualizado = ModeloCarrito.actualizar_cantidad(producto_id, cantidad)
        if actualizado:
            flash('Carrito actualizado', 'success')
        else:
            flash('No se pudo actualizar la cantidad (stock insuficiente)', 'danger')
    return redirect(url_for('user_blueprint.user_cart'))

@user.route('/carrito/eliminar/<int:id_producto>', methods=['POST', 'GET'])
@require_login
def delete_cart_item(id_producto):
    ModeloCarrito.eliminar_producto(id_producto)
    flash('Producto eliminado del carrito', 'info')
    return redirect(url_for('user_blueprint.user_cart'))

@user.route('/historial')
@require_login
def user_history():
    user_data = ModeloUsuario.get_by_id(session['user_id'])
    items = links_sidebar()
    pedidos = ModeloPedido.get_pedidos_completos_por_usuario(session['user_id'])
    return render_template(
        'profile-pedidos.html',
        items=items,
        user=user_data,
        pedidos=pedidos
    )