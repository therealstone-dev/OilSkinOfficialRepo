from src.database.db_mysql import get_connection

class ModeloAdmin:
    @classmethod
    def get_kpis_generales(cls):
        try:
            conn = get_connection()
            cur = conn.cursor()

            # Resumen de ventas e ingresos
            cur.execute("""
                SELECT 
                    total_pedidos_completados, 
                    total_ingresos, 
                    ticket_promedio 
                FROM vw_admin_resumen_kpis
            """)
            kpi_resumen = cur.fetchone() or {}

            # Resumen de inventario y bajo stock
            cur.execute("""
                SELECT 
                    COALESCE(SUM(stock), 0) AS total_unidades_inventario,
                    COALESCE(SUM(stock * precio), 0) AS valor_total_inventario,
                    COUNT(CASE WHEN stock <= 10 THEN 1 END) AS productos_bajo_stock
                FROM producto
            """)
            kpi_inventario = cur.fetchone() or {}

            cur.close()
            conn.close()

            total_ingresos = float(kpi_resumen.get('total_ingresos', 0) or 0)
            total_pedidos = int(kpi_resumen.get('total_pedidos_completados', 0) or 0)
            ticket_promedio = float(kpi_resumen.get('ticket_promedio', 0) or 0)

            return {
                'total_ingresos': total_ingresos,
                'total_pedidos': total_pedidos,
                'ticket_promedio': ticket_promedio,
                'total_unidades_inventario': int(kpi_inventario.get('total_unidades_inventario', 0) or 0),
                'valor_total_inventario': float(kpi_inventario.get('valor_total_inventario', 0) or 0),
                'productos_bajo_stock': int(kpi_inventario.get('productos_bajo_stock', 0) or 0)
            }
        except Exception as ex:
            print(f"Error en get_kpis_generales: {ex}")
            return {
                'total_ingresos': 0.0,
                'total_pedidos': 0,
                'ticket_promedio': 0.0,
                'total_unidades_inventario': 0,
                'valor_total_inventario': 0.0,
                'productos_bajo_stock': 0
            }

    @classmethod
    def get_desglose_productos(cls):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = ("""
                SELECT 
                    v.id_producto,
                    v.nombre_producto,
                    v.precio_venta,
                    v.stock_actual,
                    v.nombre_categoria,
                    p.id_categoria,
                    p.descripcion,
                    v.unidades_vendidas,
                    v.ingresos_totales_producto,
                    v.estado_stock
                FROM vw_admin_inventario_ventas v
                LEFT JOIN producto p ON p.id_producto = v.id_producto
                ORDER BY v.unidades_vendidas DESC, v.stock_actual ASC
            """)
            cur.execute(sql)
            productos = cur.fetchall()
            cur.close()
            conn.close()

            for p in productos:
                p['precio_venta'] = float(p.get('precio_venta', 0))
                p['unidades_vendidas'] = int(p.get('unidades_vendidas', 0))
                p['ingresos_totales_producto'] = float(p.get('ingresos_totales_producto', 0))
            return productos
        except Exception as ex:
            print(f"Error en get_desglose_productos: {ex}")
            return []

    @classmethod
    def get_ultimas_ventas(cls, limit=10):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = ("""
                SELECT 
                    hp.id_pedido,
                    hp.fecha_pedido,
                    hp.estado_pedido,
                    hp.pedido_subtotal,
                    hp.metodo_pago,
                    u.nombre AS cliente_nombre,
                    u.email AS cliente_email
                FROM vw_historial_pedidos hp
                LEFT JOIN usuario u ON u.id_usuario = hp.id_usuario
                ORDER BY hp.fecha_pedido DESC
                LIMIT %s
            """)
            cur.execute(sql, (limit,))
            ventas = cur.fetchall()
            cur.close()
            conn.close()

            for v in ventas:
                v['pedido_subtotal'] = float(v.get('pedido_subtotal', 0))
            return ventas
        except Exception as ex:
            print(f"Error en get_ultimas_ventas: {ex}")
            return []

    @classmethod
    def get_datos_graficas(cls):
        try:
            conn = get_connection()
            cur = conn.cursor()

            # 1. Ventas e inventario por categoría
            cur.execute("""
                SELECT 
                    COALESCE(c.nombre_categoria, 'Sin Categoría') AS categoria,
                    SUM(pr.stock) AS stock_total,
                    COALESCE(SUM(dp.cantidad), 0) AS unidades_vendidas
                FROM producto pr
                LEFT JOIN categoria c ON c.id_categoria = pr.id_categoria
                LEFT JOIN detalle_pedido dp ON dp.id_producto = pr.id_producto
                LEFT JOIN pedido p ON p.id_pedido = dp.id_pedido AND p.estado_pedido != 'cancelado'
                GROUP BY c.id_categoria, c.nombre_categoria
            """)
            cat_data = cur.fetchall()

            # 2. Distribución de Estados de Pedidos
            cur.execute("""
                SELECT 
                    COALESCE(estado_pedido, 'pendiente') AS estado,
                    COUNT(*) AS conteo
                FROM pedido
                GROUP BY estado_pedido
            """)
            pedidos_estados = cur.fetchall()

            # 3. Tendencia de Ingresos e Histórico por Fecha
            cur.execute("""
                SELECT 
                    DATE(fecha_pedido) AS fecha,
                    COUNT(id_pedido) AS total_pedidos,
                    COALESCE(SUM(subtotal), 0) AS ingresos_dia
                FROM pedido
                WHERE estado_pedido != 'cancelado'
                GROUP BY DATE(fecha_pedido)
                ORDER BY fecha ASC
                LIMIT 15
            """)
            ingresos_fechas = cur.fetchall()

            # 4. Estado de Salud del Inventario (Bajo Stock, Normal, Abundante)
            cur.execute("""
                SELECT 
                    estado_stock,
                    COUNT(*) AS cantidad_productos
                FROM vw_admin_inventario_ventas
                GROUP BY estado_stock
            """)
            estados_inv = cur.fetchall()

            # 5. Valor Comercial del Inventario vs Ingresos por Producto (Top 8)
            cur.execute("""
                SELECT 
                    nombre_producto,
                    (stock_actual * precio_venta) AS valor_inventario,
                    ingresos_totales_producto
                FROM vw_admin_inventario_ventas
                ORDER BY ingresos_totales_producto DESC, stock_actual DESC
                LIMIT 8
            """)
            prod_valor_data = cur.fetchall()

            cur.close()
            conn.close()

            categorias_nombres = [item['categoria'] for item in cat_data]
            categorias_stock = [int(item['stock_total'] or 0) for item in cat_data]
            categorias_ventas = [int(item['unidades_vendidas'] or 0) for item in cat_data]

            estados_labels = [str(item['estado']).capitalize() for item in pedidos_estados]
            estados_counts = [int(item['conteo']) for item in pedidos_estados]

            fechas_labels = [item['fecha'].strftime('%d/%m/%Y') if hasattr(item['fecha'], 'strftime') else str(item['fecha']) for item in ingresos_fechas]
            fechas_ingresos = [float(item['ingresos_dia'] or 0) for item in ingresos_fechas]
            fechas_ventas = [int(item['total_pedidos'] or 0) for item in ingresos_fechas]

            inv_estados_labels = [str(item['estado_stock']) for item in estados_inv]
            inv_estados_counts = [int(item['cantidad_productos']) for item in estados_inv]

            prod_nombres = [item['nombre_producto'] for item in prod_valor_data]
            prod_valor_inv = [float(item['valor_inventario'] or 0) for item in prod_valor_data]
            prod_ingresos = [float(item['ingresos_totales_producto'] or 0) for item in prod_valor_data]

            return {
                'categorias_nombres': categorias_nombres,
                'categorias_stock': categorias_stock,
                'categorias_ventas': categorias_ventas,
                'estados_labels': estados_labels,
                'estados_counts': estados_counts,
                'fechas_labels': fechas_labels,
                'fechas_ingresos': fechas_ingresos,
                'fechas_ventas': fechas_ventas,
                'inv_estados_labels': inv_estados_labels,
                'inv_estados_counts': inv_estados_counts,
                'prod_nombres': prod_nombres,
                'prod_valor_inv': prod_valor_inv,
                'prod_ingresos': prod_ingresos
            }
        except Exception as ex:
            print(f"Error en get_datos_graficas: {ex}")
            return {
                'categorias_nombres': [],
                'categorias_stock': [],
                'categorias_ventas': [],
                'estados_labels': [],
                'estados_counts': [],
                'fechas_labels': [],
                'fechas_ingresos': [],
                'fechas_ventas': [],
                'inv_estados_labels': [],
                'inv_estados_counts': [],
                'prod_nombres': [],
                'prod_valor_inv': [],
                'prod_ingresos': []
            }

    # ==================== GESTIÓN DE USUARIOS ====================

    @classmethod
    def get_todos_usuarios(cls):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    u.id_usuario,
                    u.nombre,
                    u.email,
                    u.celular,
                    u.direccion,
                    u.created_at,
                    u.id_rol,
                    u.activo,
                    COALESCE(r.nombre_rol, 'Cliente') AS nombre_rol
                FROM usuario u
                LEFT JOIN rol r ON r.id_rol = u.id_rol
                ORDER BY u.activo DESC, u.id_usuario DESC
            """)
            usuarios = cur.fetchall()
            cur.close()
            conn.close()
            return usuarios
        except Exception as ex:
            print(f"Error en get_todos_usuarios: {ex}")
            return []

    @classmethod
    def actualizar_rol_usuario(cls, id_usuario: int, nuevo_id_rol: int):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE usuario SET id_rol = %s WHERE id_usuario = %s", (nuevo_id_rol, id_usuario))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Rol de usuario actualizado exitosamente."
        except Exception as ex:
            print(f"Error en actualizar_rol_usuario: {ex}")
            return False, f"Error al actualizar rol: {ex}"

    @classmethod
    def eliminar_o_restringir_usuario(cls, id_usuario: int):
        """Restringe (desactiva) un usuario en vez de eliminarlo para respetar las FK."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE usuario SET activo = 0 WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Usuario restringido correctamente. Ya no podrá iniciar sesión."
        except Exception as ex:
            print(f"Error en eliminar_o_restringir_usuario: {ex}")
            return False, f"Error al restringir el usuario: {ex}"

    @classmethod
    def reactivar_usuario(cls, id_usuario: int):
        """Reactiva un usuario previamente restringido."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE usuario SET activo = 1 WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Usuario reactivado correctamente."
        except Exception as ex:
            print(f"Error en reactivar_usuario: {ex}")
            return False, f"Error al reactivar el usuario: {ex}"

    # ==================== GESTIÓN DE INVENTARIO ====================

    @classmethod
    def get_todas_categorias(cls):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id_categoria, nombre_categoria FROM categoria ORDER BY nombre_categoria ASC")
            categorias = cur.fetchall()
            cur.close()
            conn.close()
            return categorias
        except Exception as ex:
            print(f"Error en get_todas_categorias: {ex}")
            return []

    @classmethod
    def crear_producto(cls, nombre_producto: str, descripcion: str, precio: float, stock: int, id_categoria: int):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO producto (nombre_producto, descripcion, precio, stock, id_categoria)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre_producto, descripcion, precio, stock, id_categoria))
            conn.commit()
            last_id = cur.lastrowid
            cur.close()
            conn.close()
            return True, f"Producto creado con éxito (ID: {last_id})."
        except Exception as ex:
            print(f"Error en crear_producto: {ex}")
            return False, f"Error al crear producto: {ex}"

    @classmethod
    def actualizar_producto(cls, id_producto: int, nombre_producto: str, descripcion: str, precio: float, stock: int, id_categoria: int):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE producto 
                SET nombre_producto = %s, descripcion = %s, precio = %s, stock = %s, id_categoria = %s
                WHERE id_producto = %s
            """, (nombre_producto, descripcion, precio, stock, id_categoria, id_producto))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Producto actualizado con éxito."
        except Exception as ex:
            print(f"Error en actualizar_producto: {ex}")
            return False, f"Error al actualizar producto: {ex}"

    @classmethod
    def ajustar_stock_producto(cls, id_producto: int, nuevo_stock: int):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE producto SET stock = %s WHERE id_producto = %s", (nuevo_stock, id_producto))
            conn.commit()
            cur.close()
            conn.close()
            return True, f"Stock de producto #{id_producto} actualizado a {nuevo_stock} unidades."
        except Exception as ex:
            print(f"Error en ajustar_stock_producto: {ex}")
            return False, f"Error al ajustar stock: {ex}"

    @classmethod
    def eliminar_producto(cls, id_producto: int):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM producto WHERE id_producto = %s", (id_producto,))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Producto eliminado exitosamente del catálogo."
        except Exception as ex:
            print(f"Error en eliminar_producto: {ex}")
            return False, f"No se pudo eliminar el producto (puede tener compras/detalles asociados): {ex}"

    # ==================== GESTIÓN DE VENTAS E INFORMES ====================

    @classmethod
    def actualizar_estado_pedido(cls, id_pedido: int, nuevo_estado: str):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE pedido SET estado_pedido = %s WHERE id_pedido = %s", (nuevo_estado, id_pedido))
            conn.commit()
            cur.close()
            conn.close()
            return True, f"Estado del pedido #{id_pedido} actualizado a '{nuevo_estado}'."
        except Exception as ex:
            print(f"Error en actualizar_estado_pedido: {ex}")
            return False, f"Error al actualizar estado del pedido: {ex}"

    @classmethod
    def get_ventas_filtradas(cls, estado: str = None):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = """
                SELECT 
                    hp.id_pedido,
                    hp.fecha_pedido,
                    hp.estado_pedido,
                    hp.pedido_subtotal,
                    hp.metodo_pago,
                    hp.id_factura,
                    hp.direccion_entrega,
                    hp.ciudad,
                    hp.telefono_contacto,
                    hp.costo_envio,
                    hp.estado_envio,
                    hp.origen_despacho,
                    hp.lat_entrega,
                    hp.lng_entrega,
                    hp.lat_origen,
                    hp.lng_origen,
                    hp.empresa_envio,
                    hp.numero_guia,
                    hp.mensaje_transportista,
                    hp.fecha_estimada_entrega,
                    u.nombre AS cliente_nombre,
                    u.email AS cliente_email,
                    u.celular AS cliente_celular
                FROM vw_historial_pedidos hp
                LEFT JOIN usuario u ON u.id_usuario = hp.id_usuario
            """
            params = []
            if estado and estado != 'todos':
                sql += " WHERE LOWER(hp.estado_pedido) = %s"
                params.append(estado.lower())
            sql += " ORDER BY hp.fecha_pedido DESC"
            cur.execute(sql, tuple(params))
            ventas = cur.fetchall()
            cur.close()
            conn.close()
            for v in ventas:
                v['pedido_subtotal'] = float(v.get('pedido_subtotal', 0))
            return ventas
        except Exception as ex:
            print(f"Error en get_ventas_filtradas: {ex}")
            return []

    @classmethod
    def actualizar_domicilio_pedido(cls, id_pedido: int, origen_despacho: str, lat_origen: float, lng_origen: float,
                                    estado_envio: str, empresa_envio: str, numero_guia: str, mensaje_transportista: str,
                                    fecha_estimada_entrega: str = None):
        try:
            conn = get_connection()
            cur = conn.cursor()

            # Verificar si existe registro de domicilio para el pedido
            cur.execute("SELECT id_domicilio FROM domicilio WHERE id_pedido = %s", (id_pedido,))
            domicilio = cur.fetchone()

            if domicilio:
                cur.execute("""
                    UPDATE domicilio 
                    SET origen_despacho = %s,
                        lat_origen = %s,
                        lng_origen = %s,
                        estado_envio = %s,
                        empresa_envio = %s,
                        numero_guia = %s,
                        mensaje_transportista = %s,
                        fecha_estimada_entrega = %s
                    WHERE id_pedido = %s
                """, (origen_despacho, lat_origen, lng_origen, estado_envio, empresa_envio, numero_guia, mensaje_transportista, fecha_estimada_entrega, id_pedido))
            else:
                cur.execute("""
                    INSERT INTO domicilio (id_pedido, direccion_entrega, ciudad, telefono_contacto, costo_envio, estado_envio,
                                           origen_despacho, lat_origen, lng_origen, empresa_envio, numero_guia, mensaje_transportista, fecha_estimada_entrega)
                    VALUES (%s, 'Dirección principal', 'Colombia', '0000000000', 0.00, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (id_pedido, estado_envio, origen_despacho, lat_origen, lng_origen, empresa_envio, numero_guia, mensaje_transportista, fecha_estimada_entrega))

            # Si el estado de envío pasa a entregado o cancelado, sincronizar estado del pedido si corresponde
            if estado_envio == 'entregado':
                cur.execute("UPDATE pedido SET estado_pedido = 'pagado' WHERE id_pedido = %s AND estado_pedido != 'cancelado'", (id_pedido,))
            elif estado_envio == 'cancelado':
                cur.execute("UPDATE pedido SET estado_pedido = 'cancelado' WHERE id_pedido = %s", (id_pedido,))

            conn.commit()
            cur.close()
            conn.close()
            return True, f"Datos de despacho y transportista para el pedido #{id_pedido} actualizados exitosamente."
        except Exception as ex:
            print(f"Error en actualizar_domicilio_pedido: {ex}")
            return False, f"Error al actualizar datos de despacho: {ex}"

    @classmethod
    def generar_resumen_reporte_ventas(cls):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(id_pedido) AS total_pedidos,
                    COALESCE(SUM(CASE WHEN estado_pedido != 'cancelado' THEN subtotal ELSE 0 END), 0) AS ingresos_netos,
                    COALESCE(SUM(CASE WHEN estado_pedido = 'pagado' THEN 1 ELSE 0 END), 0) AS pedidos_pagados,
                    COALESCE(SUM(CASE WHEN estado_pedido = 'pendiente' THEN 1 ELSE 0 END), 0) AS pedidos_pendientes,
                    COALESCE(SUM(CASE WHEN estado_pedido = 'cancelado' THEN 1 ELSE 0 END), 0) AS pedidos_cancelados
                FROM pedido
            """)
            resumen = cur.fetchone() or {}
            cur.close()
            conn.close()
            return {
                'total_pedidos': int(resumen.get('total_pedidos', 0) or 0),
                'ingresos_netos': float(resumen.get('ingresos_netos', 0) or 0),
                'pedidos_pagados': int(resumen.get('pedidos_pagados', 0) or 0),
                'pedidos_pendientes': int(resumen.get('pedidos_pendientes', 0) or 0),
                'pedidos_cancelados': int(resumen.get('pedidos_cancelados', 0) or 0),
            }
        except Exception as ex:
            print(f"Error en generar_resumen_reporte_ventas: {ex}")
            return {'total_pedidos': 0, 'ingresos_netos': 0.0, 'pedidos_pagados': 0, 'pedidos_pendientes': 0, 'pedidos_cancelados': 0}



