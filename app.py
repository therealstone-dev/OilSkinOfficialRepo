from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_mysqldb import MySQL
from src.database.db_mysql import init_db

app=Flask(__name__)
init_db(app)

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
 