from src.database.db_mysql import get_connection
import bcrypt
import hashlib

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
        Crea un nuevo usuario. Asigna id_rol=1 (cliente).
        """
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
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
            foto_perfil = foto_perfil.strip() if (foto_perfil and isinstance(foto_perfil, str) and foto_perfil.strip()) else None
            foto_portada = foto_portada.strip() if (foto_portada and isinstance(foto_portada, str) and foto_portada.strip()) else None

            if not foto_perfil and not foto_portada:
                return False, "No se proporcionó ninguna imagen para actualizar."

            conn = get_connection()
            cur = conn.cursor()
            
            updates = []
            params = []
            if foto_perfil:
                updates.append("foto_perfil = %s")
                params.append(foto_perfil)
            if foto_portada:
                updates.append("foto_portada = %s")
                params.append(foto_portada)
                
            params.append(id_usuario)
            sql = f"UPDATE usuario SET {', '.join(updates)} WHERE id_usuario = %s"
            cur.execute(sql, tuple(params))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Imágenes de perfil actualizadas correctamente."
        except Exception as ex:
            print(f"Error en update_images: {ex}")
            return False, f"Error al actualizar imágenes: {ex}"

    @classmethod
    def update_password(cls, id_usuario, new_password):
        """Actualiza la contraseña de un usuario mediante su ID con hash seguro bcrypt."""
        try:
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            hashed_str = hashed.decode('utf-8')

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE usuario SET contrasena = %s WHERE id_usuario = %s", (hashed_str, id_usuario))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Contraseña restablecida exitosamente."
        except Exception as ex:
            print(f"Error en update_password: {ex}")
            return False, f"Error al actualizar la contraseña: {ex}"

    # ==================== MÉTODOS GOOGLE OAUTH 2.0 ====================

    @classmethod
    def get_by_google_id(cls, google_id: str):
        """Busca un usuario por su identificador único de Google."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM usuario WHERE google_id = %s", (google_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            return result
        except Exception as ex:
            print(f"Error en get_by_google_id: {ex}")
            return None

    @classmethod
    def create_google_user(cls, nombre: str, email: str, google_id: str, foto_perfil: str = None):
        """Registra un nuevo usuario autenticado vía Google OAuth 2.0."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            sql = ("INSERT INTO usuario (nombre, email, google_id, auth_provider, foto_perfil, id_rol, activo, direccion, celular) "
                   "VALUES (%s, %s, %s, 'google', %s, 1, 1, '', '')")
            cur.execute(sql, (nombre, email, google_id, foto_perfil))
            conn.commit()
            last_id = cur.lastrowid
            cur.close()
            conn.close()
            return last_id
        except Exception as ex:
            print(f"Error en create_google_user: {ex}")
            return None

    @classmethod
    def link_google_account(cls, id_usuario: int, google_id: str, foto_perfil: str = None):
        """Vincula una cuenta de Google a un usuario existente por correo."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            if foto_perfil:
                sql = "UPDATE usuario SET google_id = %s, auth_provider = 'google', foto_perfil = COALESCE(foto_perfil, %s) WHERE id_usuario = %s"
                cur.execute(sql, (google_id, foto_perfil, id_usuario))
            else:
                sql = "UPDATE usuario SET google_id = %s, auth_provider = 'google' WHERE id_usuario = %s"
                cur.execute(sql, (google_id, id_usuario))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as ex:
            print(f"Error en link_google_account: {ex}")
            return False

    # ==================== MÉTODOS CÓDIGOS OTP RECUPERACIÓN ====================

    @classmethod
    def guardar_codigo_recuperacion(cls, id_usuario: int, codigo_hash: str, minutos_validez: int = 15):
        """Guarda un código OTP hasheado invalidando cualquier código previo activo."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Invalidar códigos anteriores del usuario
            cur.execute("UPDATE codigo_recuperacion SET utilizado = 1 WHERE id_usuario = %s AND utilizado = 0", (id_usuario,))
            
            # Insertar nuevo código con expiración
            sql = """
                INSERT INTO codigo_recuperacion (id_usuario, codigo_hash, expiracion, intentos, utilizado)
                VALUES (%s, %s, NOW() + INTERVAL %s MINUTE, 0, 0)
            """
            cur.execute(sql, (id_usuario, codigo_hash, minutos_validez))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as ex:
            print(f"Error en guardar_codigo_recuperacion: {ex}")
            return False

    @classmethod
    def verificar_codigo_recuperacion(cls, email: str, codigo_plano: str):
        """
        Verifica si el código OTP coincide con el almacenado para el usuario.
        Controla intentos fallidos (máximo 5) y expiración de tiempo.
        Retorna (exito: bool, mensaje: str, usuario: dict | None).
        """
        try:
            user = cls.get_by_email(email)
            if not user:
                return False, "Usuario no encontrado.", None

            id_usuario = user.get('id_usuario') if isinstance(user, dict) else user[0]
            conn = get_connection()
            cur = conn.cursor()

            # Obtener el código activo más reciente
            sql = """
                SELECT id_codigo, codigo_hash, expiracion, intentos, utilizado,
                       (expiracion < NOW()) AS expirado
                FROM codigo_recuperacion
                WHERE id_usuario = %s AND utilizado = 0
                ORDER BY id_codigo DESC
                LIMIT 1
            """
            cur.execute(sql, (id_usuario,))
            codigo_info = cur.fetchone()

            if not codigo_info:
                cur.close()
                conn.close()
                return False, "No hay ningún código de recuperación activo. Por favor solicita uno nuevo.", None

            id_codigo = codigo_info.get('id_codigo') if isinstance(codigo_info, dict) else codigo_info[0]
            codigo_hash = codigo_info.get('codigo_hash') if isinstance(codigo_info, dict) else codigo_info[1]
            intentos = codigo_info.get('intentos', 0) if isinstance(codigo_info, dict) else codigo_info[3]
            expirado = codigo_info.get('expirado', 0) if isinstance(codigo_info, dict) else codigo_info[5]

            # Verificar si expiró
            if expirado:
                cur.execute("UPDATE codigo_recuperacion SET utilizado = 1 WHERE id_codigo = %s", (id_codigo,))
                conn.commit()
                cur.close()
                conn.close()
                return False, "El código ha expirado (validez de 15 minutos). Por favor solicita uno nuevo.", None

            # Verificar intentos máximos
            if intentos >= 5:
                cur.execute("UPDATE codigo_recuperacion SET utilizado = 1 WHERE id_codigo = %s", (id_codigo,))
                conn.commit()
                cur.close()
                conn.close()
                return False, "Has superado el límite de intentos permitidos (5). Solicita un nuevo código por seguridad.", None

            # Comparar hash
            input_hash = hashlib.sha256(codigo_plano.strip().encode('utf-8')).hexdigest()
            if input_hash == codigo_hash:
                # Marcar código como utilizado exitosamente
                cur.execute("UPDATE codigo_recuperacion SET utilizado = 1 WHERE id_codigo = %s", (id_codigo,))
                conn.commit()
                cur.close()
                conn.close()
                return True, "Código verificado correctamente.", user
            else:
                # Incrementar intentos
                nuevos_intentos = intentos + 1
                cur.execute("UPDATE codigo_recuperacion SET intentos = %s WHERE id_codigo = %s", (nuevos_intentos, id_codigo))
                conn.commit()
                cur.close()
                conn.close()
                restantes = max(0, 5 - nuevos_intentos)
                return False, f"Código incorrecto. Te quedan {restantes} {'intento' if restantes == 1 else 'intentos'}.", None

        except Exception as ex:
            print(f"Error en verificar_codigo_recuperacion: {ex}")
            return False, f"Error al procesar la verificación: {ex}", None


