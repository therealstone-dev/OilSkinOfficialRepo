from functools import wraps
from flask import redirect, session, url_for, request, flash


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_id'):
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth_blueprint.login', next=request.path))
        return view(*args, **kwargs)

    return wrapped_view
