import os
from flask import Flask
from routes import orders_blueprint
from models import inicializar_tabla_pedidos

app = Flask(__name__)
app.register_blueprint(orders_blueprint)

if __name__ == '__main__':
    inicializar_tabla_pedidos()
    puerto = int(os.getenv("PORT", 5003))
    app.run(host='0.0.0.0', port=puerto)