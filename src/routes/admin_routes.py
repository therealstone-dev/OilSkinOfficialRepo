from flask import Blueprint, render_template
from src.models.ModeloProductos import ModeloProducto
from src.models.ModeloCategoria import ModeloCategoria
from src.utils.nav_helper import get_nav_data

# Blueprint para manejar las rutas
admin = Blueprint('admin_blueprint', __name__)

@admin.route('/admin')
def admin_dashboard():
    return render_template('admin_dashboard.jinja', categorias=get_nav_data())