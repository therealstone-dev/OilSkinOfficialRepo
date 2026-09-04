import os
from datetime import timedelta
from flask import Flask
from pathlib import Path
from decouple import config
from werkzeug.middleware.proxy_fix import ProxyFix
from src.database.db_mysql import init_db
from src.routes import main_routes, auth_routes, user_routes, admin_routes

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

    # Optimizacion de cache de recursos estaticos (CSS, imagenes, JS) -Hecho con IA- no borrar porfa :v
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    @app.after_request
    def add_header(response):
        if 'Cache-Control' not in response.headers:
            if response.mimetype.startswith(('image/', 'text/css', 'application/javascript', 'font/')):
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response

    # Soporte para proxy inverso en producción (HTTPS, IP real del cliente)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    app.register_blueprint(main_routes.main, url_prefix='/')
    app.register_blueprint(auth_routes.auth, url_prefix='/auth')
    app.register_blueprint(user_routes.user, url_prefix='/usuario')
    app.register_blueprint(admin_routes.admin, url_prefix='/admin')
    
    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

 