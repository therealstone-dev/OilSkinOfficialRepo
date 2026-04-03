from src.database.db_mysql import mysql

class DBUtils:
    @classmethod
    def get_field_by_id(cls, table, field, record_id):
        """
        Obtiene un campo específico de cualquier tabla filtrando por el ID.
        :param table: Nombre de la tabla (string)
        :param field: Nombre del campo (string)
        :param record_id: El ID del registro (int/string)
        
        Donde me dañen esto los asesino
        """
        try:
            cur = mysql.connection.cursor()
            query = f"SELECT {field} FROM {table} WHERE id = %s"
            cur.execute(query, (record_id,))
            
            result = cur.fetchone()
            cur.close()

            return result[field] if result else None
            
        except Exception as ex:
            print(f"❌ Error al obtener {field} de {table}: {ex}")
            return None

# Modelo principal con metodos especificos para categorias
class ModeloProducto:
    @classmethod
    def get_all(cls):
        cur=mysql.connection.cursor()
        cur.execute("SELECT nombre_producto, descripcion, precio, stock from producto ORDER BY nombre_producto ASC")
        return cur.fetchall()
    @classmethod
    def get_by_id(cls, id_producto):
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM producto WHERE id_producto = %s", (id_producto,))
        return cur.fetchone()
    @classmethod
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
    def get_by_category_id(cls, category_id):
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT * FROM producto WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            productos = cur.fetchall()
            cur.close()
            print(f"Productos encontrados para categoría {category_id}: {len(productos)}")
            return productos
        except Exception as ex:
            print(f"Error en get_by_category_id: {ex}")
            return []
    @classmethod
    def get_categories(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT DISTINCT categoria FROM productos")
        categories = cur.fetchall()
        cur.close()
        return categories