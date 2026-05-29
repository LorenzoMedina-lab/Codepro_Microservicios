from flask import Blueprint, request, jsonify
from models import obtener_conexion_db
from auth_shared import requerir_token_autenticado
import random

delivery_blueprint = Blueprint('delivery', __name__)
# Endpoint para agendar el despacho de hielo, protegido por autenticación JWT.
@delivery_blueprint.route('/envios', methods=['POST'])
@requerir_token_autenticado
def agendar_despacho_de_hielo(usuario_contexto):
    datos = request.get_json() or {}
    pedido_id = datos.get('pedido_id')
    
    if not pedido_id:
        return jsonify({"error": "pedido_id es obligatorio"}), 400
        
    repartidores_disponibles = ["Pinguino_Veloz", "Ranger_Del_Glaciar", "Tractor_Invernal"]
    repartidor = random.choice(repartidores_disponibles)
    
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO envios (pedido_id, repartidor_asignado, estado_envio)
                VALUES (%s, %s, 'PREPARANDO_CARGA') RETURNING id;
            """, (pedido_id, repartidor))
            envio_id = cursor.fetchone()[0]
        conexion.commit()
        
    return jsonify({
        "envio_id": envio_id,
        "pedido_id": pedido_id,
        "repartidor": repartidor,
        "estado_logistica": "PREPARANDO_CARGA",
        "mensaje": "Logistica activada. El hielo esta en camino antes de licuarse."
    }), 201
# Endpoint para listar todos los envíos, protegido por autenticación JWT.
@delivery_blueprint.route('/envios', methods=['GET'])
@requerir_token_autenticado  # Barrera de seguridad JWT activa
def listar_todos_los_envios(usuario_contexto): # Recibe el contexto del token de forma obligatoria
    try:
        lista_envios = []
        
        with obtener_conexion_db() as conexion:
            with conexion.cursor() as cursor:
                # columnas reales 'repartidor_asignado' y 'estado_envio'
                cursor.execute("SELECT id, pedido_id, repartidor_asignado, estado_envio FROM envios ORDER BY id ASC;")
                envios = cursor.fetchall()
                
                # Se procesa la lista dentro del contexto seguro de la conexión
                for e in envios:
                    lista_envios.append({
                        "id": e[0],
                        "pedido_id": e[1],
                        "repartidor_asignado": e[2],
                        "estado_envio": e[3]
                    })
            
        return jsonify(lista_envios), 200
        
    except Exception as e:
        return jsonify({"error": f"Error al consultar el glaciar de envíos: {str(e)}"}), 500