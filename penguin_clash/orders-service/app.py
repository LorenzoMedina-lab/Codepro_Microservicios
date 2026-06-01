import os # Agregado para manejar variables de entorno, como el puerto en el que se ejecutará la aplicación.
from flask import Flask # Importamos Flask para crear la aplicación web.
from routes import orders_blueprint # Importamos el blueprint de rutas para los pedidos desde el módulo routes.
from models import inicializar_tabla_pedidos # Importamos la función para inicializar la tabla de pedidos desde el módulo models.

app = Flask(__name__) # Creamos una instancia de la aplicación Flask.
app.register_blueprint(orders_blueprint) # Registramos el blueprint de rutas para los pedidos en la aplicación Flask.

if __name__ == '__main__': # Verificamos si el script se está ejecutando directamente (en lugar de ser importado como un módulo).
    inicializar_tabla_pedidos() # Llamamos a la función para inicializar la tabla de pedidos en la base de datos.
    puerto = int(os.getenv("PORT", 5003)) # Obtenemos el puerto desde la variable de entorno "PORT", o usamos el puerto 5003 por defecto si no está definida.
    app.run(host='0.0.0.0', port=puerto) # Iniciamos la aplicación Flask, escuchando en todas las interfaces de red (0.0.0.0) en el puerto especificado.