from flask import Blueprint, request, jsonify # Blueprint para organizar rutas, request para manejar solicitudes, jsonify para respuestas JSON
from models import obtener_conexion_db # Función para obtener conexión a la base de datos local db_auth
from auth_shared import generar_token_jwt, requerir_token_autenticado # Decorador para proteger rutas con autenticación JWT
# Se crea un Blueprint para organizar las rutas relacionadas con autenticación
auth_blueprint = Blueprint('auth', __name__)

# Ruta para registrar un nuevo usuario
@auth_blueprint.route('/register', methods=['POST'])
def registrar_nuevo_usuario():
    datos = request.get_json() or {}
    username = datos.get('username')
    password = datos.get('password')
    rol = datos.get('rol', 'user') # Si no envían rol, por defecto es 'user'
    
    if not username or not password:
        return jsonify({"error": "Campos username y password requeridos"}), 400
        
    try:
        with obtener_conexion_db() as conexion:
            with conexion.cursor() as cursor:
                # Insertamos el nuevo usuario en la base de datos local db_auth
                cursor.execute(
                    "INSERT INTO usuarios (username, password, rol) VALUES (%s, %s, %s) RETURNING id;",
                    (username, password, rol)
                )
                nuevo_id = cursor.fetchone()[0]
            conexion.commit() # Confirmamos la transacción transaccional
            
        return jsonify({
            "mensaje": "Usuario creado con exito",
            "usuario_id": nuevo_id
        }), 201
        
    except Exception as e:
        # Por si el usuario ya existe problemas de tipos
        return jsonify({"error": f"No se pudo crear el usuario: {str(e)}"}), 500

# Ruta para autenticar usuario y entregar token JWT
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

# Ruta protegida para listar todos los usuarios (solo para administradores)
@auth_blueprint.route('/usuarios', methods=['GET'])
@requerir_token_autenticado  # Protegido por seguridad
def listar_todos_los_usuarios(usuario_contexto):
    try:
        with obtener_conexion_db() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id, username, rol FROM usuarios ORDER BY id ASC;")
                usuarios = cursor.fetchall()
                
        lista_usuarios = []
        for u in usuarios:
            lista_usuarios.append({
                "id": u[0],
                "username": u[1],
                "rol": u[2]
            })
        return jsonify(lista_usuarios), 200
    except Exception as e:
        return jsonify({"error": f"Error en la DB de auth: {str(e)}"}), 500