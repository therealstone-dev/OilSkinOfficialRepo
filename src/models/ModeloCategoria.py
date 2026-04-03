from src.database.db_mysql import mysql

class ModeloCategoria:
    @classmethod
    def get_description_by_name(cls, category_name):
        """
        Busca la descripcion de una categoria especifica por su nombre
        """
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT descripcion FROM categoria WHERE nombre = %s"
            cur.execute(sql, (category_name,))
            result = cur.fetchone()
            cur.close()
            return result['descripcion'] if result else "Sin descripción disponible."
        except Exception as ex:
            print(f"Error en ModeloCategoria: {ex}")
            return None

    @classmethod
    def get_description_by_id(cls, category_id):
        """
        Busca la descripcion de una categoria especifica por su ID
        """
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT descripcion FROM categoria WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            result = cur.fetchone()
            cur.close()
            return result['descripcion'] if result else "Sin descripción disponible."
        except Exception as ex:
            print(f"❌ Error en ModeloCategoria: {ex}")
            return None

    @classmethod
    def get_name_by_id(cls, category_id):
        """
        Busca el nombre de una categoria especifica por su ID
        """
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT nombre_categoria FROM categoria WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            result = cur.fetchone()
            cur.close()
            return result['nombre_categoria'] if result else "Categoría"
        except Exception as ex:
            print(f"Error en ModeloCategoria: {ex}")
            return None
    @classmethod
    def get_all_categories(cls):
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT nombre FROM categoria"
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            return result
        except Exception as ex:
            print(f"Error en ModeloCategoria: {ex}")
            return None