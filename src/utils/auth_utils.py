from functools import wraps
from flask import session, redirect, url_for, flash

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth_blueprint.login'))
        return f(*args, **kwargs)
    return decorated
