from src.database.db_mysql import get_connection

class ModeloPedido:
    @classmethod
    def get_pedidos_por_usuario(cls, id_usuario):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = ("""
                SELECT 
                    id_pedido, 
                    fecha_pedido, 
                    estado_pedido, 
                    pedido_subtotal,
                    id_usuario,
                    id_factura,
                    factura_subtotal,
                    factura_total,
                    metodo_pago,
                    direccion_entrega,
                    ciudad,
                    telefono_contacto,
                    costo_envio,
                    estado_envio
                FROM vw_historial_pedidos
                WHERE id_usuario = %s
                ORDER BY fecha_pedido DESC
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
                    id_detalle, 
                    id_pedido, 
                    id_producto, 
                    cantidad, 
                    precio_unitario, 
                    subtotal,
                    nombre_producto,
                    descripcion
                FROM vw_detalle_pedidos_productos
                WHERE id_pedido = %s
            """)
            cur.execute(sql, (id_pedido,))
            detalles = cur.fetchall()
            cur.close()
            conn.close()
            return detalles
        except Exception as ex:
            print(f"Error en get_detalles_pedido: {ex}")
            return []

    @classmethod
    def get_pedidos_completos_por_usuario(cls, id_usuario):
        pedidos = cls.get_pedidos_por_usuario(id_usuario)
        for pedido in pedidos:
            # Usar la clave 'productos' para evitar conflicto en Jinja2 con dict.items
            pedido['productos'] = cls.get_detalles_pedido(pedido['id_pedido'])
        return pedidos

    @classmethod
    def solicitar_reembolso(cls, id_pedido, id_usuario):
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Verificar pertenencia del pedido
            cur.execute("SELECT id_pedido, estado_pedido FROM pedido WHERE id_pedido = %s AND id_usuario = %s", (id_pedido, id_usuario))
            pedido = cur.fetchone()
            if not pedido:
                cur.close()
                conn.close()
                return False, "El pedido especificado no existe o no pertenece a tu cuenta."

            # Cambiar estado del pedido y domicilio a cancelado/reembolsado
            cur.execute("UPDATE pedido SET estado_pedido = 'cancelado' WHERE id_pedido = %s", (id_pedido,))
            cur.execute("UPDATE domicilio SET estado_envio = 'cancelado' WHERE id_pedido = %s", (id_pedido,))
            conn.commit()
            cur.close()
            conn.close()
            return True, f"Solicitud de reembolso para el pedido #OS-{id_pedido:05d} procesada correctamente."
        except Exception as ex:
            print(f"Error en solicitar_reembolso: {ex}")
            return False, f"Error al procesar solicitud: {ex}"
