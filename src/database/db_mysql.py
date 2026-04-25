import os
from decouple import config
from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    try:
        app.config['MYSQL_HOST'] = config('MYSQL_HOST')
        app.config['MYSQL_USER'] = config('MYSQL_USER')
        app.config['MYSQL_PASSWORD'] = config('MYSQL_PASSWORD')
        app.config['MYSQL_DB'] = config('MYSQL_DB')
        app.config['MYSQL_PORT'] = int(config('MYSQL_PORT', default='3306'))
        app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
        
        # Configurar SSL con certificado CA para Aiven
        ca_path = config('MYSQL_SSL_CA', default=None)
        if ca_path and os.path.exists(ca_path):
            app.config['MYSQL_CUSTOM_OPTIONS'] = {"ssl": {"ca": ca_path}}
        else:
            app.config['MYSQL_CUSTOM_OPTIONS'] = {"ssl": {"enabled": True}}
        
        mysql.init_app(app)
        print("✓ Conexión a Aiven MySQL OK")
    except Exception as error:
        print(f"✗ Error MySQL: {error}")
        raise

def get_connection():
    return mysql.connection.cursor()