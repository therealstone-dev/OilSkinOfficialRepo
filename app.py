from datetime import timedelta
from flask import Flask
from pathlib import Path
from decouple import config
from src.database.db_mysql import init_db
from src.routes import main_routes, auth_routes, user_routes

# Configuración de rutas
BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / 'src' / 'templates'
STATIC_DIR = BASE_DIR / 'src' / 'static'

def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
        static_url_path='/static'
    )

    init_db(app)

    # Seguridad: clave secreta para sesiones y CSRF
    app.secret_key = config('SECRET_KEY', default='dev-secret-key')
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.permanent_session_lifetime = timedelta(days=7)

    app.register_blueprint(main_routes.main, url_prefix='/')
    app.register_blueprint(auth_routes.auth, url_prefix='/auth')
    app.register_blueprint(user_routes.user, url_prefix='/usuario')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
 