import bcrypt

from src.database.db_mysql import get_connection


class ModeloUsuario:
    @classmethod
    def get_by_email(cls, email):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT * FROM usuario WHERE email = %s"
            cur.execute(sql, (email,))
            usuario = cur.fetchone()
            cur.close()
            conn.close()
            return usuario
        except Exception as ex:
            print(f"Error en ModeloUsuario.get_by_email: {ex}")
            return None

    @classmethod
    def get_by_id(cls, user_id):
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = "SELECT id_usuario, nombre, direccion, telefono, celular, email, id_rol FROM usuario WHERE id_usuario = %s"
            cur.execute(sql, (user_id,))
            usuario = cur.fetchone()
            cur.close()
            conn.close()
            return usuario
        except Exception as ex:
            print(f"Error en ModeloUsuario.get_by_id: {ex}")
            return None

    @classmethod
    def get_default_role_id(cls):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id_rol FROM rol ORDER BY id_rol LIMIT 1")
            result = cur.fetchone()
            if result and 'id_rol' in result:
                role_id = result['id_rol']
            else:
                role_id = cls.create_default_role(conn, cur)
            cur.close()
            conn.close()
            return role_id
        except Exception as ex:
            print(f"Error en ModeloUsuario.get_default_role_id: {ex}")
            return None

    @classmethod
    def create_default_role(cls, conn, cur):
        try:
            cur.execute(
                "INSERT INTO rol (nombre_rol, permisos) VALUES (%s, %s)",
                ("Cliente", "")
            )
            conn.commit()
            return cur.lastrowid
        except Exception as ex:
            print(f"Error en ModeloUsuario.create_default_role: {ex}")
            return None

    @classmethod
    def create(cls, nombre, email, password, direccion, celular, telefono=None, id_rol=None):
        try:
            if id_rol is None:
                id_rol = cls.get_default_role_id()

            if id_rol is None:
                print("Error en ModeloUsuario.create: no se encontró ni se pudo crear un rol predeterminado")
                return False

            hashed_password = cls.hash_password(password)
            conn = get_connection()
            cur = conn.cursor()
            sql = (
                "INSERT INTO usuario (nombre, contrasena, direccion, telefono, celular, email, id_rol) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            cur.execute(sql, (nombre, hashed_password, direccion, telefono, celular, email, id_rol))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as ex:
            print(f"Error en ModeloUsuario.create: {ex}")
            return False

    @classmethod
    def verify_password(cls, password, hashed_password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as ex:
            print(f"Error en ModeloUsuario.verify_password: {ex}")
            return False

    @classmethod
    def hash_password(cls, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
