from src.database.db_mysql import mysql

# Modelo principal con metodos especificos para categorias
class ModeloProducto:
    @classmethod
    # Obtiene todos los productos
    def get_all(cls):
        cur=mysql.connection.cursor()
        cur.execute("SELECT nombre_producto, descripcion, precio, stock from producto ORDER BY nombre_producto ASC")
        cur.close()
        return cur.fetchall()
    @classmethod
    # Obtiene un producto por su id
    def get_by_id(cls, id_producto):
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM producto WHERE id_producto = %s", (id_producto,))
        cur.close()
        return cur.fetchone()
    @classmethod
    # Obtiene todos los productos filtrados por categoria
    def get_by_category(cls, category_name):
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT * FROM producto WHERE nombre_categoria = %s"
            cur.execute(sql, (category_name,))
            productos = cur.fetchall()
            cur.close()
            return productos
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    # Obtiene productos por id de categoria
    def get_by_category_id(cls, category_id):
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT * FROM producto WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            productos = cur.fetchall()
            cur.close()
            return productos
        except Exception as ex:
            print(f"Error en get_by_category_id: {ex}")
            return []
    @classmethod
    # Obtiene los ids de categoria de los productos
    def get_categories(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_categoria FROM producto")
        categories = cur.fetchall()
        cur.close()
        return categories