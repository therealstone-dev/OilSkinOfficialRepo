from flask import session
from src.database.db_mysql import get_connection


class ModeloCarrito:
    @staticmethod
    def _get_cart_session():
        return session.setdefault('cart', [])

    @classmethod
    def agregar_producto(cls, id_producto, cantidad=1):
        cart = cls._get_cart_session()
        for item in cart:
            if item['id_producto'] == id_producto:
                item['cantidad'] += cantidad
                item['subtotal'] = round(item['cantidad'] * item['precio_unitario'], 2)
                return item

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id_producto, nombre_producto, precio, stock FROM producto WHERE id_producto = %s",
            (id_producto,),
        )
        producto = cur.fetchone()
        cur.close()
        conn.close()

        if not producto:
            return None

        if producto['stock'] < cantidad:
            return 'sin_stock'

        item = {
            'id_producto': producto['id_producto'],
            'nombre_producto': producto['nombre_producto'],
            'precio_unitario': float(producto['precio']),
            'cantidad': cantidad,
            'subtotal': round(cantidad * float(producto['precio']), 2),
        }
        cart.append(item)
        session['cart'] = cart
        return item

    @classmethod
    def obtener_carrito(cls):
        return cls._get_cart_session()

    @classmethod
    def actualizar_cantidad(cls, id_producto, cantidad):
        cart = cls._get_cart_session()
        for item in cart:
            if item['id_producto'] == id_producto:
                if cantidad <= 0:
                    cart.remove(item)
                    session['cart'] = cart
                    return True

                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT stock FROM producto WHERE id_producto = %s", (id_producto,))
                stock = cur.fetchone()
                cur.close()
                conn.close()

                if stock and stock['stock'] >= cantidad:
                    item['cantidad'] = cantidad
                    item['subtotal'] = round(item['cantidad'] * item['precio_unitario'], 2)
                    session['cart'] = cart
                    return True

                return False
        return False

    @classmethod
    def eliminar_producto(cls, id_producto):
        cart = cls._get_cart_session()
        new_cart = [item for item in cart if item['id_producto'] != id_producto]
        session['cart'] = new_cart
        return True

    @classmethod
    def vaciar(cls):
        session['cart'] = []
        return True

    @classmethod
    def total_items(cls):
        return sum(item['cantidad'] for item in cls.obtener_carrito())

    @classmethod
    def total_precio(cls):
        return round(sum(item['subtotal'] for item in cls.obtener_carrito()), 2)
