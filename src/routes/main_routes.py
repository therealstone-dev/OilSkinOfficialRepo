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
    return render_template('error_page.jinja')

# Ruta principal
@main.route('/')
def index():
    return render_template('index.jinja',categorias=get_nav_data())

@main.route('/sobre_nosotros')
def about():
    return render_template('sobre_nosotros.jinja',categorias=get_nav_data())
@main.route('/login')
def login():
    return render_template('login.jinja',categorias=get_nav_data())
@main.route('/register')
def register():
    return render_template('register.jinja',categorias=get_nav_data())

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
    productos = ModeloProducto.get_by_category_id(category_id)
    descripcion = ModeloCategoria.get_description_by_id(category_id)
    category_name = ModeloCategoria.get_name_by_id(category_id)
    
    return render_template('category.jinja', productos=productos, descripcion=descripcion, category_name=category_name,categorias=get_nav_data())    