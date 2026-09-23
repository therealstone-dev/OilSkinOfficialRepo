from src.database.db_mysql import get_connection

# Modelo principal con metodos especificos para categorias
class ModeloProducto:
    @classmethod
    # Obtiene todos los productos
    def get_all(cls, solo_activos=True):
        conn = get_connection()
        cur = conn.cursor()
        filtro = "WHERE activo = 1" if solo_activos else ""
        cur.execute(f"SELECT id_producto, nombre_producto, descripcion, precio, stock, imagenUrl, id_categoria, activo FROM producto {filtro} ORDER BY nombre_producto ASC")
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
            sql = "SELECT * FROM producto WHERE nombre_categoria = %s AND activo = 1"
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
            sql = "SELECT * FROM producto WHERE id_categoria = %s AND activo = 1"
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
        cur.execute("SELECT DISTINCT id_categoria FROM producto WHERE activo = 1")
        categories = cur.fetchall()
        cur.close()
        conn.close()
        return categories
    
    @classmethod
    def decrement_stock(cls, cur, id_producto, cantidad):
        sql = (
            'UPDATE producto '
            'SET stock = stock - %s '
            'WHERE id_producto = %s AND stock >= %s'
        )
        cur.execute(sql, (cantidad, id_producto, cantidad))
        return cur.rowcount == 1

    @classmethod
    def get_stock(cls, id_producto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT stock FROM producto WHERE id_producto = %s', (id_producto,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result['stock'] if result else None

    @classmethod
    def update_imagen(cls, id_producto: int, imagen_url: str):
        """Actualiza la imagenUrl de un producto."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE producto SET imagenUrl = %s WHERE id_producto = %s", (imagen_url, id_producto))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as ex:
            print(f"Error en ModeloProducto.update_imagen: {ex}")
            return False

    @classmethod
    def get_atributos(cls, id_producto: int):
        """
        Obtiene los atributos extendidos del producto agrupados por tipo:
        beneficio, modo_uso, ingrediente, badge
        """
        agrupados = {
            'beneficio': [],
            'modo_uso': [],
            'ingrediente': [],
            'badge': []
        }
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id_atributo, tipo, titulo, contenido, orden 
                FROM producto_atributo 
                WHERE id_producto = %s 
                ORDER BY tipo, orden ASC, id_atributo ASC
            """, (id_producto,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for r in rows:
                t = r.get('tipo')
                if t in agrupados:
                    agrupados[t].append(r)
            return agrupados
        except Exception as ex:
            print(f"Error en ModeloProducto.get_atributos: {ex}")
            return agrupados

    @classmethod
    def guardar_atributos(cls, id_producto: int, lista_atributos):
        """
        Reemplaza transaccionalmente los atributos de un producto.
        lista_atributos: lista de dicts o diccionario agrupado por tipo
        """
        try:
            items_planos = []
            if isinstance(lista_atributos, dict):
                for tipo, items in lista_atributos.items():
                    if isinstance(items, list):
                        for idx, item in enumerate(items):
                            if isinstance(item, dict):
                                item_copy = dict(item)
                                item_copy.setdefault('tipo', tipo)
                                item_copy.setdefault('orden', idx + 1)
                                items_planos.append(item_copy)
                            elif isinstance(item, str) and item.strip():
                                items_planos.append({'tipo': tipo, 'titulo': item.strip(), 'contenido': item.strip(), 'orden': idx + 1})
                    elif isinstance(items, str) and items.strip():
                        items_planos.append({'tipo': tipo, 'titulo': tipo.capitalize(), 'contenido': items.strip(), 'orden': 1})
            elif isinstance(lista_atributos, list):
                items_planos = [item for item in lista_atributos if isinstance(item, dict)]

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM producto_atributo WHERE id_producto = %s", (id_producto,))
            if items_planos:
                sql = """
                    INSERT INTO producto_atributo (id_producto, tipo, titulo, contenido, orden)
                    VALUES (%s, %s, %s, %s, %s)
                """
                params = []
                for a in items_planos:
                    tit = str(a.get('titulo') or '').strip()
                    cont = str(a.get('contenido') or '').strip()
                    if not cont and tit:
                        cont = tit
                    if tit or cont:
                        params.append((
                            id_producto,
                            a.get('tipo', 'beneficio'),
                            tit,
                            cont,
                            int(a.get('orden', 0))
                        ))
                if params:
                    cur.executemany(sql, params)
            conn.commit()
            cur.close()
            conn.close()
            return True, "Atributos del producto guardados correctamente."
        except Exception as ex:
            print(f"Error en ModeloProducto.guardar_atributos: {ex}")
            return False, f"Error al guardar atributos: {ex}"