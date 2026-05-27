import requests
import time
from flask import Blueprint, request, jsonify
from models import obtener_conexion_db
from auth_shared import requerir_token_autenticado
from config import INVENTORY_SERVICE_URL

orders_blueprint = Blueprint('orders', __name__)

def comunicarse_con_inventario_con_reintentos(url: str, json_data: dict, headers: dict, reintentos_maximos=3):
    """Implementa politica de reintentos (Retry) para tolerancia a fallos."""
    for intento in range(reintentos_maximos):
        try:
            respuesta = requests.post(url, json=json_data, headers=headers, timeout=3)
            return respuesta
        except requests.exceptions.RequestException:
            if intento == reintentos_maximos - 1:
                raise
            time.sleep(1) # Espera un segundo antes de reintentar

@orders_blueprint.route('/pedidos', methods=['POST'])
@requerir_token_autenticado
def procesar_y_crear_pedido(usuario_contexto):
    datos = request.get_json() or {}
    producto_id = datos.get('producto_id')
    cantidad = datos.get('cantidad')
    usuario_id = usuario_contexto['sub']
    
    if not producto_id or not cantidad:
        return jsonify({"error": "Faltan parametros obligatorios"}), 400

    token_original = request.headers.get("Authorization")
    headers_internos = {"Authorization": token_original}

    # 1. Recuperar info del producto para verificar precio
    try:
        url_info = f"{INVENTORY_SERVICE_URL}/productos/{producto_id}"
        respuesta_info = requests.get(url_info, timeout=3)
        if respuesta_info.status_code != 200:
            return jsonify({"error": "No se pudo obtener informacion del producto"}), respuesta_info.status_code
        
        datos_producto = respuesta_info.json()
        total_calculado = datos_producto['precio'] * cantidad
        
    except requests.exceptions.RequestException:
        return jsonify({"error": "Servicio de inventario no responde. Fallo intermitente."}), 503

    # 2. Descontar stock usando la política de reintentos distribuida
    try:
        url_descuento = f"{INVENTORY_SERVICE_URL}/productos/{producto_id}/descontar"
        respuesta_descuento = comunicarse_con_inventario_con_reintentos(
            url_descuento, {"cantidad": cantidad}, headers_internos
        )
        
        if respuesta_descuento.status_code != 200:
            error_msg = respuesta_descuento.get_json().get("error", "Error desconocido")
            return jsonify({"error": f"Fallo en reserva de inventario: {error_msg}"}), respuesta_descuento.status_code
            
    except requests.exceptions.RequestException:
        return jsonify({"error": "Inventario fuera de linea tras reintentos catastroficos."}), 503

   # 3. Registrar el pedido en la base de datos local
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pedidos (usuario_id, producto_id, cantidad, total, estado)
                VALUES (%s, %s, %s, %s, 'PROCESADO') RETURNING id;
            """, (usuario_id, producto_id, cantidad, total_calculado))
            pedido_id = cursor.fetchone()[0]
        conexion.commit()

    # 4. Comunicar al servicio de logística para agendar el despacho del hielo, con manejo de fallos
    try: #Si el servicio de logística no responde, el pedido se creó pero la logística se agendará después.
        url_delivery = "http://delivery-service:5004/envios"
        respuesta_delivery = requests.post(url_delivery, json={"pedido_id": pedido_id}, headers=headers_internos, timeout=3)
        
        if respuesta_delivery.status_code == 201: #Logística agendada correctamente
            datos_envio = respuesta_delivery.json()
            return jsonify({
                "pedido_id": pedido_id,
                "estado": "PROCESADO",
                "total": total_calculado,
                "logistica": {
                    "envio_id": datos_envio["envio_id"],
                    "repartidor": datos_envio["repartidor"],
                    "estado": datos_envio["estado_logistica"]
                },
                "mensaje": "Pedido creado y pinguino repartidor asignado correctamente."
            }), 201
    except requests.exceptions.RequestException:
        # Falla con gracia: El pedido se creó pero logística se agendará después
        return jsonify({
            "pedido_id": pedido_id,
            "estado": "PROCESADO_PENDIENTE_LOGISTICA",
            "total": total_calculado,
            "mensaje": "Pedido registrado pero el camion de hielo no responde. Reintentando internamente."
        }), 202