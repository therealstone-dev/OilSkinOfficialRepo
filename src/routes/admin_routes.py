from io import StringIO
import csv
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, Response
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
    graficas = ModeloAdmin.get_datos_graficas()
    return render_template('dashboard_metricas.html', kpis=kpis, graficas=graficas, categorias=get_nav_data())

@admin.route('/usuarios')
@require_admin
def usuarios():
    usuarios = ModeloAdmin.get_todos_usuarios()
    return render_template('dashboard_usuarios.html', usuarios=usuarios, categorias=get_nav_data())

@admin.route('/inventario')
@require_admin
def inventario():
    productos = ModeloAdmin.get_desglose_productos()
    todas_categorias = ModeloAdmin.get_todas_categorias()
    return render_template('dashboard_inventario.html', productos=productos, todas_categorias=todas_categorias, categorias=get_nav_data())

@admin.route('/ventas')
@require_admin
def ventas():
    estado_filtro = request.args.get('estado_filtro', 'todos')
    ultimas_ventas = ModeloAdmin.get_ventas_filtradas(estado=estado_filtro)
    resumen_ventas = ModeloAdmin.generar_resumen_reporte_ventas()
    return render_template('dashboard_ventas.html', ultimas_ventas=ultimas_ventas, resumen_ventas=resumen_ventas, estado_filtro=estado_filtro, categorias=get_nav_data())

# ==================== RUTAS DE GESTIÓN DE USUARIOS ====================

@admin.route('/usuarios/<int:id_usuario>/rol', methods=['POST'])
@require_admin
def cambiar_rol_usuario(id_usuario):
    nuevo_id_rol = request.form.get('id_rol', type=int)
    if not nuevo_id_rol:
        flash('Rol no válido seleccionado.', 'danger')
        return redirect(url_for('admin_blueprint.usuarios'))

    exito, mensaje = ModeloAdmin.actualizar_rol_usuario(id_usuario, nuevo_id_rol)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.usuarios'))

@admin.route('/usuarios/<int:id_usuario>/eliminar', methods=['POST'])
@require_admin
def eliminar_usuario(id_usuario):
    if id_usuario == session.get('user_id'):
        flash('No puedes restringir tu propio usuario en sesión activa.', 'danger')
        return redirect(url_for('admin_blueprint.usuarios'))

    exito, mensaje = ModeloAdmin.eliminar_o_restringir_usuario(id_usuario)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.usuarios'))

@admin.route('/usuarios/<int:id_usuario>/reactivar', methods=['POST'])
@require_admin
def reactivar_usuario(id_usuario):
    exito, mensaje = ModeloAdmin.reactivar_usuario(id_usuario)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.usuarios'))

# ==================== RUTAS DE GESTIÓN DE INVENTARIO ====================

@admin.route('/inventario/crear', methods=['POST'])
@require_admin
def crear_producto():
    nombre = request.form.get('nombre_producto', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    precio = request.form.get('precio', type=float)
    stock = request.form.get('stock', type=int)
    id_categoria = request.form.get('id_categoria', type=int)

    if not nombre or precio is None or stock is None or not id_categoria:
        flash('Por favor completa todos los campos obligatorios del producto.', 'danger')
        return redirect(url_for('admin_blueprint.inventario'))

    exito, mensaje = ModeloAdmin.crear_producto(nombre, descripcion, precio, stock, id_categoria)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.inventario'))

@admin.route('/inventario/<int:id_producto>/editar', methods=['POST'])
@require_admin
def editar_producto(id_producto):
    nombre = request.form.get('nombre_producto', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    precio = request.form.get('precio', type=float)
    stock = request.form.get('stock', type=int)
    id_categoria = request.form.get('id_categoria', type=int)

    if not nombre or precio is None or stock is None or not id_categoria:
        flash('Por favor completa todos los campos para actualizar el producto.', 'danger')
        return redirect(url_for('admin_blueprint.inventario'))

    exito, mensaje = ModeloAdmin.actualizar_producto(id_producto, nombre, descripcion, precio, stock, id_categoria)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.inventario'))

@admin.route('/inventario/<int:id_producto>/stock', methods=['POST'])
@require_admin
def ajustar_stock(id_producto):
    nuevo_stock = request.form.get('stock', type=int)
    if nuevo_stock is None or nuevo_stock < 0:
        flash('El valor de stock ingresado no es válido.', 'danger')
        return redirect(url_for('admin_blueprint.inventario'))

    exito, mensaje = ModeloAdmin.ajustar_stock_producto(id_producto, nuevo_stock)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.inventario'))

@admin.route('/inventario/<int:id_producto>/eliminar', methods=['POST'])
@require_admin
def eliminar_producto(id_producto):
    exito, mensaje = ModeloAdmin.eliminar_producto(id_producto)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.inventario'))

# ==================== RUTAS DE GESTIÓN DE VENTAS E INFORMES ====================

@admin.route('/ventas/<int:id_pedido>/estado', methods=['POST'])
@require_admin
def cambiar_estado_pedido(id_pedido):
    nuevo_estado = request.form.get('estado_pedido', '').strip()
    if not nuevo_estado:
        flash('Estado no seleccionado.', 'danger')
        return redirect(url_for('admin_blueprint.ventas'))

    exito, mensaje = ModeloAdmin.actualizar_estado_pedido(id_pedido, nuevo_estado)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.ventas'))

@admin.route('/reportes/ventas/exportar')
@require_admin
def exportar_reporte_ventas():
    ventas = ModeloAdmin.get_ventas_filtradas(estado='todos')
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID Pedido', 'Cliente', 'Email', 'Fecha Pedido', 'Método Pago', 'Estado', 'Monto Total COP'])

    for v in ventas:
        cw.writerow([
            f"#OS-{v.get('id_pedido', 0):05d}",
            v.get('cliente_nombre', 'N/A'),
            v.get('cliente_email', 'N/A'),
            v.get('fecha_pedido', ''),
            v.get('metodo_pago', ''),
            v.get('estado_pedido', ''),
            f"{v.get('pedido_subtotal', 0):.2f}"
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=reporte_ventas_oilskin.csv"}
    )
