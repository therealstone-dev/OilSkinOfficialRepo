from flask import Blueprint, render_template, session, redirect, url_for, flash
from pathlib import Path
from src.utils.nav_helper import get_nav_data
from src.utils.auth_utils import require_admin
from src.models.ModeloAdmin import ModeloAdmin

template_dir = Path(__file__).parent.parent / 'templates' / 'admin'
admin = Blueprint('admin_blueprint', __name__, url_prefix='/admin', template_folder=str(template_dir))

@admin.app_errorhandler(404)
def handle_not_found(error):
    return render_template('error_page.jinja', mensaje=error, categorias=get_nav_data())

@admin.route('/dashboard')
@require_admin
def dashboard():
    kpis = ModeloAdmin.get_kpis_generales()
    productos = ModeloAdmin.get_desglose_productos()
    ultimas_ventas = ModeloAdmin.get_ultimas_ventas(limit=10)
    graficas = ModeloAdmin.get_datos_graficas()

    return render_template(
        'dashboard.html',
        kpis=kpis,
        productos=productos,
        ultimas_ventas=ultimas_ventas,
        graficas=graficas,
        categorias=get_nav_data()
    )

