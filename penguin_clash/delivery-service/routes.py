from flask import Blueprint, request, jsonify
from models import obtener_conexion_db
from auth_shared import requerir_token_autenticado
import random

delivery_blueprint = Blueprint('delivery', __name__)

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