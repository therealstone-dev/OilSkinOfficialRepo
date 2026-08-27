import os
from app import app

# Punto de entrada WSGI para servidores de producción (Gunicorn, uWSGI, etc.)
# Expone la instancia 'app' de Flask ya inicializada

if __name__ == '__main__':
    # Permite ejecutar el servidor leyendo el puerto dinámico de la nube ($PORT)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
