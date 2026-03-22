from decouple import config
from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    try:
        app.config['MYSQL_HOST'] = config('MYSQL_HOST', default='localhost')
        app.config['MYSQL_USER'] = config('MYSQL_USER')
        app.config['MYSQL_PASSWORD'] = config('MYSQL_PASSWORD')
        app.config['MYSQL_DB'] = config('MYSQL_DB')

        app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

        mysql.init_app(app)
        print("Conexion a MySQL realizada exitosamente.")
    except Exception as error:
        print(f"Error al cargar la configuracion de MySQL: {error}")

def get_connection():
    return mysql.connection.cursor()