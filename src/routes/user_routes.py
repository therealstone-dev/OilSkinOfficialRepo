import os
import uuid
import traceback
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, url_for, session, request, redirect, flash, current_app
from pathlib import Path

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
from src.utils.nav_helper import get_nav_data
from src.utils.auth_utils import require_login
from src.models.ModeloUsuario import ModeloUsuario
from src.models.ModeloCarrito import ModeloCarrito
from src.models.ModeloPedido import ModeloPedido
from src.services.facturacion_service import FacturacionService
from src.database.db_mysql import get_connection
    
# Blueprint para manejar las rutas
template_dir = Path(__file__).parent.parent / 'templates' / 'profile'
user = Blueprint('user_blueprint', __name__, url_prefix='/usuario', template_folder=str(template_dir))

def links_sidebar():
    items = [
        {"name": "Perfil Principal", "url": url_for('user_blueprint.profile'), "icon": "fa-regular fa-circle-user"},
        {"name": "Carrito de Compras", "url": url_for('user_blueprint.user_cart'), "icon": "fa-solid fa-cart-shopping"},
        {"name": "Pedidos Realizados", "url": url_for('user_blueprint.user_history'), "icon": "fa-solid fa-clock-rotate-left"}
    ]
    if ModeloCarrito.total_items() > 0:
        items.append({"name": "Finalizar Pedido", "url": url_for('user_blueprint.user_checkout'), "icon": "fa-solid fa-credit-card"})
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

@user.route('/actualizar-imagenes', methods=['POST'])
@require_login
def update_profile_images():
    user_id = session['user_id']
    active_tab = request.form.get('active_tab', 'all')
    
    foto_perfil = None
    foto_portada = None

    # Directorio para guardar subidas de imágenes dentro del static_folder de Flask
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profiles')
    os.makedirs(upload_folder, exist_ok=True)

    # 1. Foto de Perfil (Avatar)
    if active_tab in ('avatar', 'all'):
        if 'foto_perfil_file' in request.files:
            file = request.files['foto_perfil_file']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(upload_folder, filename))
                foto_perfil = f"/static/uploads/profiles/{filename}"
        
        if not foto_perfil:
            url_val = request.form.get('foto_perfil_url', '').strip() or request.form.get('foto_perfil', '').strip()
            if url_val:
                foto_perfil = url_val

    # 2. Portada (Banner)
    if active_tab in ('banner', 'all'):
        if 'foto_portada_file' in request.files:
            file = request.files['foto_portada_file']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"banner_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(upload_folder, filename))
                foto_portada = f"/static/uploads/profiles/{filename}"
        
        if not foto_portada:
            url_val = request.form.get('foto_portada_url', '').strip() or request.form.get('foto_portada', '').strip()
            if url_val:
                foto_portada = url_val

    if not foto_perfil and not foto_portada:
        flash('Por favor selecciona una imagen para subir o ingresa una URL válida.', 'warning')
        return redirect(url_for('user_blueprint.profile'))

    exito, mensaje = ModeloUsuario.update_images(
        id_usuario=user_id,
        foto_perfil=foto_perfil,
        foto_portada=foto_portada
    )
    if exito:
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

@user.route('/checkout', methods=['GET', 'POST'])
@require_login
def user_checkout():
    user_id = session['user_id']
    user_data = ModeloUsuario.get_by_id(user_id)
    items = links_sidebar()
    carrito = ModeloCarrito.obtener_carrito()

    if not carrito:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for('user_blueprint.user_cart'))

    if request.method == 'POST':
        metodo_pago = request.form.get('metodo_pago', 'efectivo')
        direccion_entrega = request.form.get('direccion_entrega', '').strip()
        ciudad = request.form.get('ciudad', 'Bogotá').strip()
        telefono_contacto = request.form.get('telefono_contacto', '').strip()

        if not direccion_entrega or not ciudad or not telefono_contacto:
            flash('Completa todos los datos de entrega', 'danger')
            return redirect(url_for('user_blueprint.user_checkout'))

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO pedido (estado_pedido, subtotal, id_usuario) VALUES (%s, %s, %s)",
                ('pendiente', ModeloCarrito.total_precio(), user_id),
            )
            pedido_id = cur.lastrowid

            for item in carrito:
                cur.execute(
                    "INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (pedido_id, item['id_producto'], item['cantidad'], item['precio_unitario'], item['subtotal']),
                )

            lat_entrega = request.form.get('lat_entrega', type=float)
            lng_entrega = request.form.get('lng_entrega', type=float)
            origen_despacho = request.form.get('origen_despacho', 'Centro de Distribución OilSkin - Bogotá D.C.').strip() or 'Centro de Distribución OilSkin - Bogotá D.C.'
            lat_origen = request.form.get('lat_origen', default=4.6533, type=float)
            lng_origen = request.form.get('lng_origen', default=-74.0836, type=float)
            empresa_envio = 'OilSkin Express Logistics'
            numero_guia = f"OS-GUIA-{pedido_id:05d}"
            mensaje_transportista = "Pedido registrado y confirmado. Paquete en proceso de alistamiento y control de calidad en bodega."

            cur.execute(
                """INSERT INTO domicilio (
                    id_pedido, direccion_entrega, ciudad, telefono_contacto, costo_envio, estado_envio,
                    origen_despacho, lat_entrega, lng_entrega, lat_origen, lng_origen,
                    empresa_envio, numero_guia, mensaje_transportista, fecha_estimada_entrega
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (pedido_id, direccion_entrega, ciudad, telefono_contacto, 0.00, 'pendiente',
                 origen_despacho, lat_entrega, lng_entrega, lat_origen, lng_origen,
                 empresa_envio, numero_guia, mensaje_transportista, '2-4 días hábiles'),
            )

            factura = FacturacionService.crear_desde_pedido(
                id_pedido=pedido_id,
                id_usuario=user_id,
                metodo_pago=metodo_pago,
                items=[
                    {
                        'id_producto': item['id_producto'],
                        'descripcion': item['nombre_producto'],
                        'cantidad': item['cantidad'],
                        'precio_unitario': item['precio_unitario'],
                    }
                    for item in carrito
                ],
                descuento=0.00,
                conn=conn,
                cur=cur,
            )

            conn.commit()
            cur.close()
            conn.close()

            ModeloCarrito.vaciar()
            flash('¡Compra realizada con éxito! Tu pedido ha sido procesado.', 'success')
            return redirect(url_for('user_blueprint.user_history'))

        except Exception as ex:
            if 'conn' in locals():
                try:
                    conn.rollback()
                    conn.close()
                except Exception:
                    pass
            traceback.print_exc()
            flash(f'Error al procesar la compra: {ex}', 'danger')
            return redirect(url_for('user_blueprint.user_cart'))

    return render_template(
        'profile-checkout.html',
        items=items,
        user=user_data,
        carrito=carrito,
        total_items=ModeloCarrito.total_items(),
        total_precio=ModeloCarrito.total_precio()
    )

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

@user.route('/pedido/<int:id_pedido>/reembolso', methods=['POST'])
@require_login
def solicitar_reembolso(id_pedido):
    exito, mensaje = ModeloPedido.solicitar_reembolso(id_pedido, session['user_id'])
    if exito:
        flash(mensaje, 'success')
    else:
        flash(mensaje, 'danger')
    return redirect(url_for('user_blueprint.user_history'))