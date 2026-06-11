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