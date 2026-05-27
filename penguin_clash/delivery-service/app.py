import os
from flask import Flask
from routes import delivery_blueprint
from models import inicializar_tabla_envios

app = Flask(__name__)
app.register_blueprint(delivery_blueprint)

if __name__ == '__main__':
    inicializar_tabla_envios()
    puerto = int(os.getenv("PORT", 5004))
    app.run(host='0.0.0.0', port=puerto)