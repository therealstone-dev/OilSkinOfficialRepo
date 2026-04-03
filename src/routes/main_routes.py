# Todo lo que esta aqui merece un refactor urgente
# Tambien modular todo esto de forma correcta

from flask import Blueprint, render_template
from src.models.ModeloProductos import ModeloProducto
from src.models.ModeloCategoria import ModeloCategoria
from src.utils.nav_helper import get_nav_data

# Blueprint para manejar las rutas
main = Blueprint('product_blueprint', __name__)

# Ruta principal
@main.route('/')
def index():
    try:
        return render_template('index.jinja',categorias=get_nav_data())
    except Exception as Error:
        return render_template('error_page.jinja', mensaje=f"Pagina No Encontrada, {Error}")

@main.route('/sobre_nosotros')
def about():
    try:
        return render_template('sobre_nosotros.jinja',categorias=get_nav_data())
    except Exception as Error:
        return render_template('error_page.jinja', mensaje=f"Pagina No Encontrada, {Error}")

# Ruta dinamica con el id de un producto, requiere un cambio al campo de nombre_producto

@main.route('/producto/<int:id>')
def get_product(id):
    producto = ModeloProducto.get_by_id(id)
    if producto:
        return render_template('detalle.jinja', producto=producto)
    return render_template('error_page.jinja', mensaje=f"Producto no Encontrado")

# Lo mismo que arriba
@main.route('/categoria/<int:category_id>')
def show_category(category_id):
    try:
        productos = ModeloProducto.get_by_category_id(category_id)
        descripcion = ModeloCategoria.get_description_by_id(category_id)
        category_name = ModeloCategoria.get_name_by_id(category_id)
        
        return render_template('category.jinja', productos=productos, descripcion=descripcion, category_name=category_name,categorias=get_nav_data())
    except Exception as ex:
        return render_template('error_page.jinja', mensaje=f"Error al cargar categoría: {ex}")    