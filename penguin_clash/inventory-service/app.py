import os
from flask import Flask
from routes import inventory_blueprint
from models import inicializar_tabla_inventario

app = Flask(__name__)
app.register_blueprint(inventory_blueprint)

if __name__ == '__main__':
    inicializar_tabla_inventario()
    puerto = int(os.getenv("PORT", 5002))
    app.run(host='0.0.0.0', port=puerto)