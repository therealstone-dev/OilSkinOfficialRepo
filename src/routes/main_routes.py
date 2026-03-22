from flask import Blueprint, render_template
from src.models.ModeloProductos import ModeloProducto

main = Blueprint('product_blueprint', __name__)

@main.route('/')
def index():
    try:
        return render_template('index.jinja')
    except Exception as Error:
        return render_template('error_page', mensaje=f"Pagina No Encontrada, {Error}")

@main.route('/producto/<int:id>')
def get_product(id):
    producto = ModeloProducto.get_by_id(id)
    if producto:
        return render_template('detalle.html', producto=producto)
    return render_template('error_page', mensaje=f"Producto no Encontrado")