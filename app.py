from flask import Flask
from pathlib import Path
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
    app.register_blueprint(main_routes.main, url_prefix='/')
    app.register_blueprint(auth_routes.auth, url_prefix='/auth')
    app.register_blueprint(user_routes.user, url_prefix='/usuario')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
 