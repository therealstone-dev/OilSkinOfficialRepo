# Todo lo que esta aqui merece un refactor urgente
# Tambien modular todo esto de forma correcta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from src.models.ModeloCarrito import ModeloCarrito
from src.models.ModeloProductos import ModeloProducto
from src.models.ModeloCategoria import ModeloCategoria
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
        try:
            conn = ModeloProducto._get_connection() if hasattr(ModeloProducto, '_get_connection') else None
        except Exception:
            conn = None

        if conn is None:
            flash('No se pudo procesar el pedido en este momento', 'danger')
            return redirect(url_for('main_blueprint.carrito'))

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO pedido (estado_pedido, subtotal, id_usuario) VALUES (%s, %s, %s)",
                    ('pendiente', ModeloCarrito.total_precio(), session.get('user_id', 1)),
                )
                pedido_id = cur.lastrowid

                for item in carrito:
                    cur.execute(
                        "INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                        (pedido_id, item['id_producto'], item['cantidad'], item['precio_unitario'], item['subtotal']),
                    )

                conn.commit()
        except Exception as ex:
            conn.rollback()
            flash(f'Error al procesar el pedido: {ex}', 'danger')
            return redirect(url_for('main_blueprint.carrito'))
        finally:
            conn.close()

        ModeloCarrito.vaciar()
        flash('Compra realizada con éxito', 'success')
        return redirect(url_for('main_blueprint.index'))

    return _render_with_cart(
        'checkout.jinja',
        carrito=carrito,
        total_items=ModeloCarrito.total_items(),
        total_precio=ModeloCarrito.total_precio(),
    )