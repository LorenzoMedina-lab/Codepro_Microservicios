from flask import Blueprint, request, jsonify
from models import obtener_conexion_db
from auth_shared import generar_token_jwt

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['POST'])
def autenticar_usuario_y_entregar_token():
    datos = request.get_json() or {}
    username = datos.get('username')
    password = datos.get('password')
    
    if not username or not password:
        return jsonify({"error": "Campos username y password requeridos"}), 400
        
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT id, rol FROM usuarios WHERE username = %s AND password = %s;", 
                (username, password)
            )
            usuario = cursor.fetchone()
            
    if usuario:
        usuario_id, rol = usuario
        token = generar_token_jwt(usuario_id, rol)
        return jsonify({"token": token, "tipo": "Bearer"}), 200
        
    return jsonify({"error": "Credenciales invalidas en el backend"}), 401