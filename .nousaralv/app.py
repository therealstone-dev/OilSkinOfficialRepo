from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_mysqldb import MySQL

app=Flask(__name__)

# Config de MySql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '8GG99AqkFvKprRp('
app.config['MYSQL_DB'] = 'defiv'

#Variable que alberga la conexion
conexion = MySQL(app)

@app.before_request
def before_request():
    print("Antes de la peticion...")

@app.after_request
def after_request(response):
    print("Despues de la peticion")
    return response
# Pasar valores a una vista, como crear una vista, url personalizada, como funciona.
@app.route("/")
def index():
    lenguajes = ['PHP', 'JavaScript', 'Java', 'Lua', 'Kotlin', 'Dart']
    data={
        'titulo': 'Index',
        'bienvenida': 'Saludos',
        'lenguajes': lenguajes,
        'numeroLenguajes': len(lenguajes)
    }
    return render_template('index.jinja', data=data)


# Url dinamica y mostrar contenido en base a esa url
@app.route("/contacto/<nombre>/<int:edad>")
def contacto(nombre,edad): 
     data={
          'titulo':'Contacto',
          'nombre': nombre,
          'edad': edad
     }
     return render_template('contacto.jinja', data=data)


# Agregar parametros a una url (query string)
def query_string():
    print(request)
    print(request.args)
    print(request.args.get('param1'))
    print(request.args.get('param2'))
    return "ok"


# Coso para mostrar productos en base a una db mysql
@app.route('/productos')
def listar_productos():
    # Creamos lista para crear datos y modificarlos a nuestras necesidades
    data={}
    # Un try-catch para hacer las operaciones cuidadosamente
    try:
        # Creamos un cursor para seleccionar y manejar la conexion
        cursor=conexion.connection.cursor()
        # Usamos una variable para almacenar la consulta o operacion SQL
        sql="SELECT nombre_producto, descripcion, precio, stock from producto ORDER BY nombre_producto ASC"
        #Con el cursor ejecutamos la operacion SQL
        cursor.execute(sql)
        # Tomamos el resultado de la operacion
        productos=cursor.fetchall()
        # Con la lista que creamos anteriormente guardamos los resultados y mostramos un mensaje de exito para saber si funciono
        data['productos'] = productos
        data['mensaje']='Exito'

        return jsonify(data)
    except Exception as ex:
        # Si no funciono, mostramos mensaje de error
        data['mensaje']='Error...'
        return data['mensaje']
# Error 404 para urls inexistentes
def pagina_no_encontrada(error):
    #return render_template('404.jinja'), 404
    return redirect(url_for('index'))



if __name__ ==  '__main__':
     # Regla de url dinamica para que funcione y aja
     app.add_url_rule('/query_string', view_func=query_string)
     #Handler del error de url inexistente
     app.register_error_handler(404,pagina_no_encontrada)
     app.run(debug=True, port=5000)
 