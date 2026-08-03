from src.database.db_mysql import get_connection
import bcrypt

class ModeloUsuario:
    @classmethod
    def get_by_email(cls, email):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM usuario WHERE email = %s", (email,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            return result
        except Exception as ex:
            print(f"Error en get_by_email: {ex}")
            return None

    @classmethod
    def get_by_id(cls, id_usuario):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            return result
        except Exception as ex:
            print(f"Error en get_by_id: {ex}")
            return None

    @classmethod
    def create(cls, nombre, email, password, direccion, celular, telefono=None, id_rol=1):
        """
        Crea un nuevo usuario. Por defecto asigna id_rol=1 (cliente). Ajusta si tu DB usa otro id.
        """
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            # Guardar como string
            hashed_str = hashed.decode('utf-8')

            conn = get_connection()
            cur = conn.cursor()
            sql = ("INSERT INTO usuario (nombre, contrasena, direccion, telefono, celular, email, id_rol) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s)")
            cur.execute(sql, (nombre, hashed_str, direccion, telefono, celular, email, id_rol))
            conn.commit()
            last_id = cur.lastrowid
            cur.close()
            conn.close()
            return last_id
        except Exception as ex:
            print(f"Error en create usuario: {ex}")
            return None

    @classmethod
    def verify_password(cls, email, password):
        try:
            user = cls.get_by_email(email)
            if not user:
                return False, None
            stored = user.get('contrasena') if isinstance(user, dict) else user[2]
            # stored is str
            if isinstance(stored, str):
                stored_bytes = stored.encode('utf-8')
            else:
                stored_bytes = stored
            ok = bcrypt.checkpw(password.encode('utf-8'), stored_bytes)
            return ok, user
        except Exception as ex:
            print(f"Error en verify_password: {ex}")
            return False, None

    @classmethod
    def update_profile(cls, id_usuario, nombre, email, direccion, celular, telefono=None):
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Verificar si el email ya pertenece a otro usuario
            cur.execute("SELECT id_usuario FROM usuario WHERE email = %s AND id_usuario != %s", (email, id_usuario))
            existing = cur.fetchone()
            if existing:
                cur.close()
                conn.close()
                return False, "El correo electrónico ya está registrado por otro usuario."

            sql = ("UPDATE usuario SET nombre = %s, email = %s, direccion = %s, "
                   "celular = %s, telefono = %s WHERE id_usuario = %s")
            cur.execute(sql, (nombre, email, direccion, celular, telefono, id_usuario))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Perfil actualizado con éxito."
        except Exception as ex:
            print(f"Error en update_profile: {ex}")
            return False, f"Error al actualizar perfil: {ex}"

    @classmethod
    def update_images(cls, id_usuario, foto_perfil=None, foto_portada=None):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = ("UPDATE usuario SET foto_perfil = COALESCE(%s, foto_perfil), "
                   "foto_portada = COALESCE(%s, foto_portada) WHERE id_usuario = %s")
            cur.execute(sql, (foto_perfil, foto_portada, id_usuario))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Imágenes de perfil actualizadas correctamente."
        except Exception as ex:
            print(f"Error en update_images: {ex}")
            return False, f"Error al actualizar imágenes: {ex}"
