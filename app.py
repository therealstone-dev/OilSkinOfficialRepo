from flask import Flask
from src.database.db_mysql import init_db
from src.routes import main_routes
import os

def create_app():
    # Obtener la ruta base absoluta
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, 'src', 'templates')
    
    # Crear la app especificando el template folder
    app = Flask(__name__, template_folder=template_dir)

    init_db(app)

    app.register_blueprint(main_routes.main, url_prefix='/')

    return app

if __name__ == '__main__':
     app = create_app()
     app.run(debug=True, port=5000)
 