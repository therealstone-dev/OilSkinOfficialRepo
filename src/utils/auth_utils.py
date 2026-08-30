from functools import wraps
from flask import session, redirect, url_for, flash
from src.database.db_mysql import get_connection

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth_blueprint.login'))
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Debes iniciar sesión para acceder al panel de administración', 'warning')
            return redirect(url_for('auth_blueprint.login'))

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id_rol FROM usuario WHERE id_usuario = %s", (user_id,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            id_rol = user.get('id_rol') if isinstance(user, dict) else (user[0] if user else None)
            if not user or id_rol != 2:
                flash('Acceso denegado. Se requieren permisos de Administrador.', 'danger')
                return redirect(url_for('main_blueprint.index'))
        except Exception as ex:
            print(f"Error comprobando permisos de admin: {ex}")
            flash('Error al verificar permisos de acceso', 'danger')
            return redirect(url_for('main_blueprint.index'))

        return f(*args, **kwargs)
    return decorated
