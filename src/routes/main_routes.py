# Todo lo que esta aqui merece un refactor urgente
# Tambien modular todo esto de forma correcta

import base64
import io
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for, Response
import traceback
import qrcode
from src.database.db_mysql import get_connection
from src.models.ModeloCarrito import ModeloCarrito
from src.models.ModeloProductos import ModeloProducto
from src.models.ModeloCategoria import ModeloCategoria
from src.services.facturacion_service import FacturacionService
from src.models.ModeloUsuario import ModeloUsuario
from src.utils.nav_helper import get_nav_data


def _render_with_cart(template_name, **context):
    context.setdefault('categorias', get_nav_data())
    context['cart_items'] = ModeloCarrito.total_items()
    return render_template(template_name, **context)

# Blueprint para manejar las rutas
main = Blueprint('main_blueprint', __name__)

@main.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja',mensaje=error, categorias=get_nav_data())

# Ruta principal
@main.route('/')
def index():
    return _render_with_cart('index.jinja')

@main.route('/sobre_nosotros')
def about():
    return _render_with_cart('sobre_nosotros.jinja')
# Ruta dinámica con el id de un producto, requiere un cambio al campo de nombre_producto

@main.route('/producto/<int:id>')
def get_product(id):
    producto = ModeloProducto.get_by_id(id)
    if producto:
        return _render_with_cart('detalle.jinja', producto=producto)
    return _render_with_cart('error_page.jinja', mensaje='Producto no encontrado')

# Ruta de categoría por nombre
@main.route('/categoria/<string:category_name>')
def show_category(category_name):
    categoria = ModeloCategoria.get_by_name(category_name)
    
    if categoria:
        productos = ModeloProducto.get_by_category_id(categoria['id_categoria'])
        
        return _render_with_cart('category.jinja', 
                               productos=productos, 
                               descripcion=categoria['descripcion'], 
                               category_name=categoria['nombre_categoria'])
    else:
        return _render_with_cart('error_page.jinja', mensaje='Categoría no encontrada')

#ruta de carrito
@main.route('/carrito')
def carrito():
    carrito = ModeloCarrito.obtener_carrito()
    return _render_with_cart(
        'carrito.jinja',
        carrito=carrito,
        total_items=ModeloCarrito.total_items(),
        total_precio=ModeloCarrito.total_precio(),
    )

@main.route('/factura/<int:id_factura>')
def ver_factura(id_factura):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT f.id_factura, f.id_pedido, f.fecha_factura, f.subtotal, f.total, f.metodo_pago, p.estado_pedido, p.id_usuario, '
        'u.nombre AS cliente_nombre, u.email AS cliente_email, u.celular AS cliente_celular, d.direccion_entrega, d.ciudad '
        'FROM factura f '
        'JOIN pedido p ON p.id_pedido = f.id_pedido '
        'LEFT JOIN usuario u ON u.id_usuario = p.id_usuario '
        'LEFT JOIN domicilio d ON d.id_pedido = p.id_pedido '
        'WHERE f.id_factura = %s',
        (id_factura,),
    )
    factura = cur.fetchone()
    items = []
    if factura:
        cur.execute(
            'SELECT dp.id_producto, p.nombre_producto AS descripcion, dp.cantidad, dp.precio_unitario, dp.subtotal '
            'FROM detalle_pedido dp JOIN producto p ON p.id_producto = dp.id_producto WHERE dp.id_pedido = %s',
            (factura['id_pedido'],),
        )
        items = cur.fetchall()
    cur.close()
    conn.close()
    if not factura:
        return _render_with_cart('error_page.jinja', mensaje='Factura no encontrada')

    qr_payload = request.host_url.rstrip('/') + url_for('main_blueprint.ver_factura', id_factura=factura['id_factura'])
    qr_buffer = io.BytesIO()
    qrcode.make(qr_payload).save(qr_buffer, format='PNG')
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('ascii')

    return render_template(
        'ver_factura.html',
        factura=factura,
        items=items,
        qr_image_data=qr_base64,
        categorias=get_nav_data(),
    )


@main.route('/factura/<int:id_factura>/pdf')
def descargar_factura_pdf(id_factura):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT f.id_factura, f.id_pedido, f.fecha_factura, f.subtotal, f.total, f.metodo_pago, p.estado_pedido, p.id_usuario, '
        'u.nombre AS cliente_nombre, u.email AS cliente_email, u.celular AS cliente_celular, d.direccion_entrega, d.ciudad '
        'FROM factura f '
        'JOIN pedido p ON p.id_pedido = f.id_pedido '
        'LEFT JOIN usuario u ON u.id_usuario = p.id_usuario '
        'LEFT JOIN domicilio d ON d.id_pedido = p.id_pedido '
        'WHERE f.id_factura = %s',
        (id_factura,),
    )
    factura = cur.fetchone()
    items = []
    if factura:
        cur.execute(
            'SELECT dp.id_producto, p.nombre_producto AS descripcion, dp.cantidad, dp.precio_unitario, dp.subtotal '
            'FROM detalle_pedido dp JOIN producto p ON p.id_producto = dp.id_producto WHERE dp.id_pedido = %s',
            (factura['id_pedido'],),
        )
        items = cur.fetchall()
    cur.close()
    conn.close()
    if not factura:
        return _render_with_cart('error_page.jinja', mensaje='Factura no encontrada')

    fecha_fmt = factura['fecha_factura'].strftime('%d/%m/%Y %H:%M') if hasattr(factura['fecha_factura'], 'strftime') else str(factura['fecha_factura'])

    factura_pdf = {
        'id_factura': factura['id_factura'],
        'numero_factura': f'FAC-2026-{factura["id_factura"]:06d}',
        'estado_factura': factura['estado_pedido'],
        'fecha_factura': fecha_fmt,
        'subtotal': float(factura['subtotal']),
        'total': float(factura['total']),
        'metodo_pago': factura['metodo_pago'],
        'cliente_nombre': factura.get('cliente_nombre') or 'Cliente General',
        'cliente_email': factura.get('cliente_email') or '',
        'cliente_celular': factura.get('cliente_celular') or '',
        'direccion_entrega': factura.get('direccion_entrega') or '',
        'ciudad': factura.get('ciudad') or '',
    }

    pdf_bytes = FacturacionService.construir_pdf_factura(
        factura=factura_pdf,
        items=[{
            'descripcion': item['descripcion'],
            'cantidad': item['cantidad'],
            'precio_unitario': float(item['precio_unitario']),
            'total_linea': float(item['subtotal']),
        } for item in items],
        base_url=request.host_url.rstrip('/'),
    )
    return Response(pdf_bytes, mimetype='application/pdf', headers={
        'Content-Disposition': f'attachment; filename={factura_pdf["numero_factura"]}.pdf'
    })


@main.route('/carrito/agregar', methods=['POST'])
def agregar_al_carrito():
    producto_id = request.form.get('producto_id', type=int)
    cantidad = request.form.get('cantidad', type=int, default=1)

    if not producto_id:
        flash('Producto inválido', 'danger')
        return redirect(url_for('main_blueprint.index'))

    resultado = ModeloCarrito.agregar_producto(producto_id, cantidad)
    if resultado == 'sin_stock':
        flash('No hay suficiente stock para este producto', 'danger')
    elif resultado:
        flash('Producto agregado al carrito', 'success')
    else:
        flash('No se encontró el producto', 'danger')

    return redirect(request.referrer or url_for('main_blueprint.index'))


@main.route('/carrito/actualizar', methods=['POST'])
def actualizar_carrito():
    producto_id = request.form.get('producto_id', type=int)
    cantidad = request.form.get('cantidad', type=int)

    if not producto_id or cantidad is None:
        flash('Datos inválidos', 'danger')
        return redirect(url_for('main_blueprint.carrito'))

    actualizado = ModeloCarrito.actualizar_cantidad(producto_id, cantidad)
    if actualizado:
        flash('Carrito actualizado', 'success')
    else:
        flash('No se pudo actualizar la cantidad', 'danger')

    return redirect(url_for('main_blueprint.carrito'))


@main.route('/carrito/eliminar/<int:id_producto>', methods=['GET', 'POST'])
def eliminar_del_carrito(id_producto):
    ModeloCarrito.eliminar_producto(id_producto)
    flash('Producto eliminado del carrito', 'info')
    return redirect(url_for('main_blueprint.carrito'))


@main.route('/checkout', methods=['GET', 'POST'])
def checkout():
    carrito = ModeloCarrito.obtener_carrito()
    if not carrito:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for('main_blueprint.carrito'))

    if request.method == 'POST':
        metodo_pago = request.form.get('metodo_pago', 'efectivo')
        direccion_entrega = request.form.get('direccion_entrega', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        telefono_contacto = request.form.get('telefono_contacto', '').strip()

        if not direccion_entrega or not ciudad or not telefono_contacto:
            flash('Completa los datos de entrega', 'danger')
            return redirect(url_for('main_blueprint.checkout'))

        try:
            usuario_id = session.get('user_id')
            if usuario_id is None:
                usuario_id = 1
            elif not ModeloUsuario.get_by_id(usuario_id):
                usuario_id = 1

            usuario_existente = ModeloUsuario.get_by_id(usuario_id)
            if not usuario_existente:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute('SELECT id_rol FROM rol LIMIT 1')
                rol = cur.fetchone()
                if rol:
                    cur.execute(
                        'INSERT INTO usuario (nombre, contrasena, direccion, telefono, celular, email, id_rol) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        ('Cliente base', 'temp', 'Sin dirección', '0000000000', '0000000000', f'cliente-{usuario_id}-{int(datetime.now().timestamp())}@example.com', rol['id_rol']),
                    )
                    conn.commit()
                    usuario_id = cur.lastrowid
                else:
                    usuario_id = None
                cur.close()
                conn.close()

            if usuario_id is None:
                raise RuntimeError('No existe un usuario válido para asociar el pedido')

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO pedido (estado_pedido, subtotal, id_usuario) VALUES (%s, %s, %s)",
                ('pendiente', ModeloCarrito.total_precio(), usuario_id),
            )
            pedido_id = cur.lastrowid

            for item in carrito:
                cur.execute(
                    "INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (pedido_id, item['id_producto'], item['cantidad'], item['precio_unitario'], item['subtotal']),
                )

            cur.execute(
                "INSERT INTO domicilio (id_pedido, direccion_entrega, ciudad, telefono_contacto, costo_envio, estado_envio) VALUES (%s, %s, %s, %s, %s, %s)",
                (pedido_id, direccion_entrega, ciudad, telefono_contacto, 0.00, 'pendiente'),
            )

            factura = FacturacionService.crear_desde_pedido(
                id_pedido=pedido_id,
                id_usuario=usuario_id,
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
        except Exception as ex:
            if 'conn' in locals():
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
            print('Error al procesar el pedido')
            traceback.print_exc()
            flash(f'Error al procesar el pedido: {ex}', 'danger')
            return redirect(url_for('main_blueprint.carrito'))

        ModeloCarrito.vaciar()
        flash('Compra realizada con éxito. Tu pedido ha sido registrado en tu panel.', 'success')
        return redirect(url_for('user_blueprint.user_history'))

    return _render_with_cart(
        'checkout.jinja',
        carrito=carrito,
        total_items=ModeloCarrito.total_items(),
        total_precio=ModeloCarrito.total_precio(),
    )