import os
from decouple import config
from flask_mysqldb import MySQL

# Establecemos una constante con la instancia de flask_mysqldb
mysql = MySQL()

# Creamos una funcion para inicializar la base de datos, le pasamos la instancia de la aplicacion principal
def init_db(app):
    # Usamos un try-except para realizar la conexion exitosamente
    try:
        # Establecemos las credenciales de nuestro host de mysql
        app.config['MYSQL_HOST'] = config('MYSQL_HOST')
        app.config['MYSQL_USER'] = config('MYSQL_USER')
        app.config['MYSQL_PASSWORD'] = config('MYSQL_PASSWORD')
        app.config['MYSQL_DB'] = config('MYSQL_DB')
        app.config['MYSQL_PORT'] = int(config('MYSQL_PORT', default='3306'))
        # Esta configuracion sirve para convertir los resultados de todas las consultas sql en diccionarios y no tuplas, muy util :)
        app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
        
        # Configurar SSL con certificado CA para Aiven
        ca_path = config('MYSQL_SSL_CA', default=None)
        # Verificamos si el certificado existe en la ruta especificada
        if ca_path and os.path.exists(ca_path):
            app.config['MYSQL_CUSTOM_OPTIONS'] = {"ssl": {"ca": ca_path}}
        else:
            app.config['MYSQL_CUSTOM_OPTIONS'] = {"ssl": {"enabled": True}}
        
        mysql.init_app(app)
        print("✓ Conexión a Aiven MySQL OK")
    # En caso de que no funcione, la aplicacion se detiene
    except Exception as error:
        print(f"✗ Error MySQL: {error}")
        raise