from src.database.db_mysql import get_connection

class ModeloCategoria:
    @classmethod
    # Obtiene la descripcion de una categoria en base al id
    def get_description_by_id(cls, category_id):
        """
        Busca la descripcion de una categoria especifica por su ID
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT descripcion FROM categoria WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
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
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT nombre_categoria FROM categoria WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
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
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT id_categoria, nombre_categoria FROM categoria ORDER BY id_categoria"
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            conn.close()
            return result if result else []
        except Exception as ex:
            print(f"Error en get_all_categories: {ex}")
            return []
    @classmethod
    def get_by_name(cls, category_name):
        """
        Obtiene todos los datos de una categoría buscando por su nombre
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT id_categoria, nombre_categoria, descripcion FROM categoria WHERE nombre_categoria = %s"
            cur.execute(sql, (category_name,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            return result
        except Exception as ex:
            print(f"Error en ModeloCategoria.get_by_name: {ex}")
            return None

    @classmethod
    def get_by_id(cls, category_id: int):
        """
        Obtiene los datos completos de una categoría por su ID
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT id_categoria, nombre_categoria, descripcion FROM categoria WHERE id_categoria = %s"
            cur.execute(sql, (category_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            return result
        except Exception as ex:
            print(f"Error en ModeloCategoria.get_by_id: {ex}")
            return None

    @classmethod
    def get_categorias_con_conteo(cls):
        """
        Obtiene todas las categorías junto con el conteo de productos asociados
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = """
                SELECT 
                    c.id_categoria, 
                    c.nombre_categoria, 
                    c.descripcion, 
                    COUNT(p.id_producto) AS total_productos
                FROM categoria c
                LEFT JOIN producto p ON p.id_categoria = c.id_categoria
                GROUP BY c.id_categoria, c.nombre_categoria, c.descripcion
                ORDER BY c.nombre_categoria ASC
            """
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            conn.close()
            return result if result else []
        except Exception as ex:
            print(f"Error en get_categorias_con_conteo: {ex}")
            return []

    @classmethod
    def crear_categoria(cls, nombre_categoria: str, descripcion: str = ""):
        """
        Inserta una nueva categoría evitando nombres duplicados
        """
        if not nombre_categoria or not str(nombre_categoria).strip():
            return False, "El nombre de la categoría es obligatorio."
        
        nombre_clean = str(nombre_categoria).strip()
        if len(nombre_clean) > 100:
            return False, "El nombre de la categoría no puede exceder 100 caracteres."
        desc_clean = str(descripcion or "").strip()

        try:
            conn = get_connection()
            cur = conn.cursor()
            # Verificar duplicados
            cur.execute("SELECT id_categoria FROM categoria WHERE LOWER(nombre_categoria) = LOWER(%s)", (nombre_clean,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return False, f"Ya existe una categoría registrada con el nombre '{nombre_clean}'."

            cur.execute(
                "INSERT INTO categoria (nombre_categoria, descripcion) VALUES (%s, %s)",
                (nombre_clean, desc_clean)
            )
            conn.commit()
            last_id = cur.lastrowid
            cur.close()
            conn.close()
            return True, f"Categoría '{nombre_clean}' creada exitosamente (ID: #{last_id})."
        except Exception as ex:
            print(f"Error en crear_categoria: {ex}")
            return False, f"Error en la base de datos: {ex}"

    @classmethod
    def actualizar_categoria(cls, id_categoria: int, nombre_categoria: str, descripcion: str = ""):
        """
        Actualiza los datos de una categoría validando que no colisione con otra
        """
        if not nombre_categoria or not str(nombre_categoria).strip():
            return False, "El nombre de la categoría no puede estar vacío."
        
        nombre_clean = str(nombre_categoria).strip()
        if len(nombre_clean) > 100:
            return False, "El nombre de la categoría no puede exceder 100 caracteres."
        desc_clean = str(descripcion or "").strip()

        try:
            conn = get_connection()
            cur = conn.cursor()
            # Verificar duplicados en otras categorías
            cur.execute(
                "SELECT id_categoria FROM categoria WHERE LOWER(nombre_categoria) = LOWER(%s) AND id_categoria != %s",
                (nombre_clean, id_categoria)
            )
            if cur.fetchone():
                cur.close()
                conn.close()
                return False, f"Ya existe otra categoría registrada con el nombre '{nombre_clean}'."

            cur.execute(
                "UPDATE categoria SET nombre_categoria = %s, descripcion = %s WHERE id_categoria = %s",
                (nombre_clean, desc_clean, id_categoria)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True, "Categoría actualizada con éxito."
        except Exception as ex:
            print(f"Error en actualizar_categoria: {ex}")
            return False, f"Error al actualizar la categoría: {ex}"

    @classmethod
    def eliminar_categoria(cls, id_categoria: int):
        """
        Elimina una categoría verificando que no tenga productos asociados para proteger la integridad
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Verificar si tiene productos asociados
            cur.execute("SELECT COUNT(*) AS total FROM producto WHERE id_categoria = %s", (id_categoria,))
            row = cur.fetchone()
            total_prods = row['total'] if row else 0

            if total_prods > 0:
                cur.close()
                conn.close()
                return False, f"No es posible eliminar la categoría porque tiene {total_prods} producto(s) asociado(s). Reasigna o elimina los productos primero."

            cur.execute("DELETE FROM categoria WHERE id_categoria = %s", (id_categoria,))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Categoría eliminada exitosamente."
        except Exception as ex:
            print(f"Error en eliminar_categoria: {ex}")
            return False, f"Error al eliminar categoría: {ex}"