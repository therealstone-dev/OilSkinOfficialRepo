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
                    id_producto,
                    nombre_producto,
                    precio_venta,
                    stock_actual,
                    nombre_categoria,
                    unidades_vendidas,
                    ingresos_totales_producto,
                    estado_stock
                FROM vw_admin_inventario_ventas
                ORDER BY unidades_vendidas DESC, stock_actual ASC
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


