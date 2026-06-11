from src.database.db_mysql import get_connection

# Modelo principal con metodos especificos para categorias
class ModeloProducto:
    @classmethod
    # Obtiene todos los productos
    def get_all(cls):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT nombre_producto, descripcion, precio, stock from producto ORDER BY nombre_producto ASC")
        result = cur.fetchall()
        cur.close()
        conn.close()
        return result
    @classmethod
    # Obtiene un producto por su id
    def get_by_id(cls, id_producto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM producto WHERE id_producto = %s", (id_producto,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result
    @classmethod
    # Obtiene todos los productos filtrados por categoria
    def get_by_category(cls, category_name):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT * FROM producto WHERE nombre_categoria = %s"
            cur.execute(sql, (category_name,))
            productos = cur.fetchall()
            cur.close()
            conn.close()
            return productos
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    # Obtiene productos por id de categoria
    def get_by_category_id(cls, category_id):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT * FROM producto WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            productos = cur.fetchall()
            cur.close()
            conn.close()
            return productos
        except Exception as ex:
            print(f"Error en get_by_category_id: {ex}")
            return []
    @classmethod
    # Obtiene los ids de categoria de los productos
    def get_categories(cls):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id_categoria FROM producto")
        categories = cur.fetchall()
        cur.close()
        conn.close()
        return categories