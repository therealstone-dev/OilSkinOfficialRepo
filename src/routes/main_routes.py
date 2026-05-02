# Todo lo que esta aqui merece un refactor urgente
# Tambien modular todo esto de forma correcta

from flask import Blueprint, render_template
from src.models.ModeloProductos import ModeloProducto
from src.models.ModeloCategoria import ModeloCategoria
from src.utils.nav_helper import get_nav_data

# Blueprint para manejar las rutas
main = Blueprint('main_blueprint', __name__)

@main.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja',mensaje=error, categorias=get_nav_data())

# Ruta principal
@main.route('/')
def index():
    return render_template('index.jinja',categorias=get_nav_data())

@main.route('/sobre_nosotros')
def about():
    return render_template('sobre_nosotros.jinja',categorias=get_nav_data())
# Ruta dinámica con el id de un producto, requiere un cambio al campo de nombre_producto

@main.route('/producto/<int:id>')
def get_product(id):
    producto = ModeloProducto.get_by_id(id)
    if producto:
        return render_template('detalle.jinja', producto=producto)
    return render_template('error_page.jinja', mensaje=f"Producto no Encontrado")

# Ruta de categoría por nombre
@main.route('/categoria/<string:category_name>')
def show_category(category_name):
    categoria = ModeloCategoria.get_by_name(category_name)
    
    if categoria:
        productos = ModeloProducto.get_by_category_id(categoria['id_categoria'])
        
        return render_template('category.jinja', 
                               productos=productos, 
                               descripcion=categoria['descripcion'], 
                               category_name=categoria['nombre_categoria'],
                               categorias=get_nav_data())
    else:
        return render_template('error_page.jinja', mensaje="Categoría no encontrada")