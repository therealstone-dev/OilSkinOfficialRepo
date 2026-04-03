from flask import Blueprint, render_template
from src.models.ModeloProductos import ModeloProducto
from src.models.ModeloCategoria import ModeloCategoria

main = Blueprint('product_blueprint', __name__)

@main.route('/')
def index():
    try:
        return render_template('index.jinja')
    except Exception as Error:
        return render_template('error_page.jinja', mensaje=f"Pagina No Encontrada, {Error}")

@main.route('/sobre_nosotros')
def about():
    try:
        return render_template('sobre_nosotros.jinja')
    except Exception as Error:
        return render_template('error_page.jinja', mensaje=f"Pagina No Encontrada, {Error}")

@main.route('/producto/<int:id>')
def get_product(id):
    producto = ModeloProducto.get_by_id(id)
    if producto:
        return render_template('detalle.jinja', producto=producto)
    return render_template('error_page.jinja', mensaje=f"Producto no Encontrado")

@main.route('/categoria/<int:category_id>')
def show_category(category_id):
    try:
        productos = ModeloProducto.get_by_category_id(category_id)
        descripcion = ModeloCategoria.get_description_by_id(category_id)
        category_name = ModeloCategoria.get_name_by_id(category_id)
        
        return render_template('category.jinja', productos=productos, descripcion=descripcion, category_name=category_name)
    except Exception as ex:
        return render_template('error_page.jinja', mensaje=f"Error al cargar categoría: {ex}")    