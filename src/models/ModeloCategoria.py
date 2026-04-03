from src.database.db_mysql import mysql

class ModeloCategoria:
    @classmethod
    # Obtiene la descripcion de una categoria en base al id
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
            print(f"Error en ModeloCategoria: {ex}")
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
        """
        Obtiene todas las categorias con id y nombre
        """
        try:
            cur = mysql.connection.cursor()
            sql = "SELECT id_categoria, nombre_categoria FROM categoria ORDER BY id_categoria"
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            return result if result else []
        except Exception as ex:
            print(f"Error en get_all_categories: {ex}")
            return []