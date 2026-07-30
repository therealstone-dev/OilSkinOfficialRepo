from src.database.db_mysql import get_connection

class ModeloPedido:
    @classmethod
    def get_pedidos_por_usuario(cls, id_usuario):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = ("""
                SELECT 
                    p.id_pedido, 
                    p.fecha_pedido, 
                    p.estado_pedido, 
                    p.subtotal AS pedido_subtotal,
                    f.id_factura,
                    f.subtotal AS factura_subtotal,
                    f.total AS factura_total,
                    f.metodo_pago,
                    d.direccion_entrega,
                    d.ciudad,
                    d.telefono_contacto,
                    d.costo_envio,
                    d.estado_envio
                FROM pedido p
                LEFT JOIN factura f ON f.id_pedido = p.id_pedido
                LEFT JOIN domicilio d ON d.id_pedido = p.id_pedido
                WHERE p.id_usuario = %s
                ORDER BY p.fecha_pedido DESC
            """)
            cur.execute(sql, (id_usuario,))
            pedidos = cur.fetchall()
            cur.close()
            conn.close()
            return pedidos
        except Exception as ex:
            print(f"Error en get_pedidos_por_usuario: {ex}")
            return []

    @classmethod
    def get_detalles_pedido(cls, id_pedido):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = ("""
                SELECT 
                    dp.id_detalle, 
                    dp.id_pedido, 
                    dp.id_producto, 
                    dp.cantidad, 
                    dp.precio_unitario, 
                    dp.subtotal,
                    pr.nombre_producto,
                    pr.descripcion
                FROM detalle_pedido dp
                JOIN producto pr ON pr.id_producto = dp.id_producto
                WHERE dp.id_pedido = %s
            """)
            cur.execute(sql, (id_pedido,))
            items = cur.fetchall()
            cur.close()
            conn.close()
            return items
        except Exception as ex:
            print(f"Error en get_detalles_pedido: {ex}")
            return []

    @classmethod
    def get_pedidos_completos_por_usuario(cls, id_usuario):
        pedidos = cls.get_pedidos_por_usuario(id_usuario)
        for pedido in pedidos:
            pedido['items'] = cls.get_detalles_pedido(pedido['id_pedido'])
        return pedidos
