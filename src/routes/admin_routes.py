from io import StringIO
import os
import uuid
import csv
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, Response, jsonify, current_app
from pathlib import Path
from src.utils.nav_helper import get_nav_data
from src.utils.auth_utils import require_admin
from src.models.ModeloAdmin import ModeloAdmin
from src.models.ModeloCategoria import ModeloCategoria
from src.models.ModeloProductos import ModeloProducto
from src.services.geolocalizacion_service import (
    geocodificar_direccion,
    validar_coordenadas,
    normalizar_direccion
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def procesar_subida_imagen_producto(req):
    """Procesa la subida de un archivo de imagen o retorna la URL provista"""
    if 'imagen_file' in req.files:
        file = req.files['imagen_file']
        if file and file.filename != '' and allowed_file(file.filename):
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'productos')
            os.makedirs(upload_folder, exist_ok=True)
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"prod_{uuid.uuid4().hex[:10]}.{ext}"
            file.save(os.path.join(upload_folder, filename))
            return f"/static/uploads/productos/{filename}"

    # URL manual alternativa
    url_val = req.form.get('imagen_url', '').strip() or req.form.get('imagenUrl', '').strip()
    return url_val if url_val else None

def extraer_atributos_desde_form(form):
    """Extrae atributos configurables de la ficha de producto desde el formulario"""
    atributos = []
    # Badges
    badges_raw = form.get('atributos_badges', '').strip()
    if badges_raw:
        for b in [x.strip() for x in badges_raw.split(',') if x.strip()]:
            atributos.append({'tipo': 'badge', 'titulo': 'Badge', 'contenido': b, 'orden': 0})

    # Beneficios
    beneficios_titulos = form.getlist('beneficio_titulo[]')
    beneficios_desc = form.getlist('beneficio_desc[]')
    for i, desc in enumerate(beneficios_desc):
        if desc.strip():
            tit = beneficios_titulos[i].strip() if i < len(beneficios_titulos) else ''
            atributos.append({'tipo': 'beneficio', 'titulo': tit, 'contenido': desc.strip(), 'orden': i + 1})

    beneficio_texto = form.get('atributo_beneficio_general', '').strip()
    if beneficio_texto and not beneficios_desc:
        atributos.append({'tipo': 'beneficio', 'titulo': 'Beneficio Principal', 'contenido': beneficio_texto, 'orden': 1})

    # Modo de Uso
    uso_pasos = form.getlist('modo_uso_paso[]')
    uso_desc = form.getlist('modo_uso_desc[]')
    for i, desc in enumerate(uso_desc):
        if desc.strip():
            tit = uso_pasos[i].strip() if i < len(uso_pasos) else f"Paso {i+1}"
            atributos.append({'tipo': 'modo_uso', 'titulo': tit, 'contenido': desc.strip(), 'orden': i + 1})

    uso_texto = form.get('atributo_modo_uso_general', '').strip()
    if uso_texto and not uso_desc:
        atributos.append({'tipo': 'modo_uso', 'titulo': 'Rutina Recomendada', 'contenido': uso_texto, 'orden': 1})

    # Ingredientes
    ingredientes_texto = form.get('atributo_ingredientes', '').strip()
    if ingredientes_texto:
        atributos.append({'tipo': 'ingrediente', 'titulo': 'Fórmula e Ingredientes', 'contenido': ingredientes_texto, 'orden': 1})

    return atributos


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

# ==================== RUTAS DE GESTIÓN DE CATEGORÍAS ====================

@admin.route('/categorias')
@require_admin
def categorias():
    categorias_con_conteo = ModeloCategoria.get_categorias_con_conteo()
    return render_template('dashboard_categorias.html', categorias_lista=categorias_con_conteo, categorias=get_nav_data())

@admin.route('/categorias/crear', methods=['POST'])
@require_admin
def crear_categoria():
    nombre = request.form.get('nombre_categoria', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    if not nombre:
        flash('El nombre de la categoría es obligatorio.', 'danger')
        return redirect(url_for('admin_blueprint.categorias'))

    exito, mensaje = ModeloCategoria.crear_categoria(nombre, descripcion)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.categorias'))

@admin.route('/categorias/<int:id_categoria>/editar', methods=['POST'])
@require_admin
def editar_categoria(id_categoria):
    nombre = request.form.get('nombre_categoria', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    if not nombre:
        flash('El nombre de la categoría es obligatorio.', 'danger')
        return redirect(url_for('admin_blueprint.categorias'))

    exito, mensaje = ModeloCategoria.actualizar_categoria(id_categoria, nombre, descripcion)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.categorias'))

@admin.route('/categorias/<int:id_categoria>/eliminar', methods=['POST'])
@require_admin
def eliminar_categoria(id_categoria):
    exito, mensaje = ModeloCategoria.eliminar_categoria(id_categoria)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_blueprint.categorias'))

# ==================== RUTAS DE GESTIÓN DE INVENTARIO ====================

@admin.route('/inventario/<int:id_producto>/atributos', methods=['GET'])
@require_admin
def obtener_atributos_producto(id_producto):
    atributos = ModeloProducto.get_atributos(id_producto)
    return jsonify(atributos)

@admin.route('/inventario/crear', methods=['POST'])
@require_admin
def crear_producto():
    nombre = request.form.get('nombre_producto', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    precio = request.form.get('precio', type=float)
    stock = request.form.get('stock', type=int)
    id_categoria = request.form.get('id_categoria', type=int)
    imagen_url = procesar_subida_imagen_producto(request)

    if not nombre or precio is None or stock is None or not id_categoria:
        flash('Por favor completa todos los campos obligatorios del producto.', 'danger')
        return redirect(url_for('admin_blueprint.inventario'))

    exito, mensaje, nuevo_id = ModeloAdmin.crear_producto(nombre, descripcion, precio, stock, id_categoria, imagen_url)
    if exito and nuevo_id:
        atributos = extraer_atributos_desde_form(request.form)
        if atributos:
            ModeloProducto.guardar_atributos(nuevo_id, atributos)

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
    imagen_url = procesar_subida_imagen_producto(request)

    if not nombre or precio is None or stock is None or not id_categoria:
        flash('Por favor completa todos los campos para actualizar el producto.', 'danger')
        return redirect(url_for('admin_blueprint.inventario'))

    exito, mensaje = ModeloAdmin.actualizar_producto(id_producto, nombre, descripcion, precio, stock, id_categoria, imagen_url)
    if exito:
        atributos = extraer_atributos_desde_form(request.form)
        ModeloProducto.guardar_atributos(id_producto, atributos)

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

@admin.route('/ventas/<int:id_pedido>/domicilio', methods=['POST'])
@require_admin
def actualizar_domicilio_pedido(id_pedido):
    origen_despacho = request.form.get('origen_despacho', '').strip() or 'Centro de Distribución OilSkin - Colegio Técnico José Félix Restrepo, Bogotá'
    lat_origen = request.form.get('lat_origen', default=4.57409, type=float)
    lng_origen = request.form.get('lng_origen', default=-74.08958, type=float)
    estado_envio = request.form.get('estado_envio', 'pendiente').strip()
    empresa_envio = request.form.get('empresa_envio', 'OilSkin Express Logistics').strip()
    numero_guia = request.form.get('numero_guia', '').strip() or f"OS-GUIA-{id_pedido:05d}"
    mensaje_transportista = request.form.get('mensaje_transportista', '').strip() or 'Pedido en proceso de despacho.'
    fecha_estimada_entrega = request.form.get('fecha_estimada_entrega', '2-4 días hábiles').strip()

    direccion_entrega = request.form.get('direccion_entrega', '').strip()
    ciudad = request.form.get('ciudad', '').strip()
    lat_entrega = request.form.get('lat_entrega', type=float)
    lng_entrega = request.form.get('lng_entrega', type=float)

    if direccion_entrega:
        direccion_entrega = normalizar_direccion(direccion_entrega)
        # Si las coordenadas de entrega no son válidas o el admin modificó la dirección, recalcular
        if not validar_coordenadas(lat_entrega, lng_entrega, ciudad):
            geo = geocodificar_direccion(direccion_entrega, ciudad=ciudad or 'Bogotá')
            lat_entrega = geo['lat']
            lng_entrega = geo['lng']

    exito, mensaje = ModeloAdmin.actualizar_domicilio_pedido(
        id_pedido=id_pedido,
        origen_despacho=origen_despacho,
        lat_origen=lat_origen,
        lng_origen=lng_origen,
        estado_envio=estado_envio,
        empresa_envio=empresa_envio,
        numero_guia=numero_guia,
        mensaje_transportista=mensaje_transportista,
        fecha_estimada_entrega=fecha_estimada_entrega,
        direccion_entrega=direccion_entrega or None,
        ciudad=ciudad or None,
        lat_entrega=lat_entrega,
        lng_entrega=lng_entrega
    )
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
