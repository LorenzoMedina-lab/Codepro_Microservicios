import os
from flask import Flask
from routes import auth_blueprint
from models import inicializar_tabla_usuarios

app = Flask(__name__)
app.register_blueprint(auth_blueprint, url_prefix='/auth')

if __name__ == '__main__':
    inicializar_tabla_usuarios()
    puerto = int(os.getenv("PORT", 5001))
    app.run(host='0.0.0.0', port=puerto)