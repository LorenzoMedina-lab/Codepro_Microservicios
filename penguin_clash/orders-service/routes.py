import time
import logging
import requests
from flask import Blueprint, request, jsonify
from models import obtener_conexion_db
from auth_shared import requerir_token_autenticado
from config import INVENTORY_SERVICE_URL

# Configuración básica de logging para monitoreo y depuración

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Definición del Blueprint para organizar las rutas relacionadas con pedidos
orders_blueprint = Blueprint('orders', __name__)

# Función auxiliar para implementar política de reintentos al comunicarse con el servicio de inventario
def comunicarse_con_inventario_con_reintentos(url: str, json_data: dict, headers: dict, reintentos_maximos=3):
    """
    Implementa política de reintentos (Retry) con respaldo de tiempo 
    para mitigar fallos intermitentes de red.
    """
    for intento in range(reintentos_maximos):
        try:
            logging.info(f"Intentando comunicación con Inventario. Intento {intento + 1} de {reintentos_maximos}")
            respuesta = requests.post(url, json=json_data, headers=headers, timeout=3)
            return respuesta
        except requests.exceptions.RequestException as e:
            logging.warning(f"Intento {intento + 1} falló debido a problemas de red: {str(e)}")
            if intento == reintentos_maximos - 1:
                raise # Repercute la excepción si se agotaron los cartuchos
            time.sleep(1) # Espera un segundo de gracia antes de reintentar

# Endpoint principal para procesar la creación de un pedido con validación de autenticación y manejo robusto de fallas
@orders_blueprint.route('/pedidos', methods=['POST'])
@requerir_token_autenticado # Decorador para validar el token JWT y extraer el contexto del usuario
def procesar_y_crear_pedido(usuario_contexto): # El contexto del usuario se inyecta automáticamente por el decorador.
    datos = request.get_json() or {} # Manejo robusto de casos donde el cuerpo de la petición no es JSON o está vacío
    producto_id = datos.get('producto_id') # Extracción de parámetros con manejo de casos donde no se proporcionan o son del tipo incorrecto
    cantidad = datos.get('cantidad') # Extracción de parámetros con manejo de casos donde no se proporcionan o son del tipo incorrecto
    
    # Extrae el ID usando la clave exacta inyectada por tu decorador
    usuario_id = usuario_contexto.get('sub') or usuario_contexto.get('usuario_id') 

    # Validación de entrada con mensajes de error claros y códigos HTTP adecuados
    if producto_id is None or cantidad is None:
        logging.warning("Estructura de petición rechazada: Parámetros ausentes.") # Logueo específico para casos de parámetros faltantes
        return jsonify({"error": "Bad Request", "mensaje": "Faltan parámetros obligatorios: 'producto_id' y 'cantidad'."}), 400

    if not isinstance(producto_id, int) or not isinstance(cantidad, int) or cantidad <= 0:
        logging.warning("Estructura de petición rechazada: Datos con tipo o valor inválido.") # Logueo específico para casos de datos inválidos
        return jsonify({"error": "Unprocessable Entity", "mensaje": "Los parámetros deben ser enteros y la cantidad mayor a cero."}), 422

    # Preparación de cabeceras para propagación del Token (Token Forwarding)
    token_original = request.headers.get("Authorization")
    headers_internos = {"Authorization": token_original}

    # 1. Recuperar info del producto para verificar precio y calcular total (Manejo de fallas con mensajes claros)
    try:
        url_info = f"{INVENTORY_SERVICE_URL}/productos/{producto_id}"
        respuesta_info = requests.get(url_info, headers=headers_internos, timeout=3)
        
        if respuesta_info.status_code != 200:
            logging.error(f"Error al localizar producto {producto_id}. Código HTTP: {respuesta_info.status_code}")
            return jsonify({"error": "No se pudo obtener información del producto o no existe"}), respuesta_info.status_code
        
        datos_producto = respuesta_info.json()
        total_calculado = datos_producto['precio'] * cantidad
        
    except requests.exceptions.RequestException:
        logging.error("Fallo de conexión sincrónica al intentar leer datos del catálogo.")
        return jsonify({"error": "Servicio de inventario no responde. Fallo transitorio."}), 503

    # 2. Descontar stock usando la política de reintentos para manejar fallas intermitentes de red o del servicio de inventario
    try:
        url_descuento = f"{INVENTORY_SERVICE_URL}/productos/{producto_id}/descontar"
        respuesta_descuento = comunicarse_con_inventario_con_reintentos(
            url_descuento, {"cantidad": cantidad}, headers_internos
        )
        
        if respuesta_descuento.status_code != 200:
            # Corrección del método: .json() en lugar de .get_json()
            try:
                error_msg = respuesta_descuento.json().get("error", "Error desconocido")
            except Exception:
                error_msg = "Error al parsear respuesta de inventario"
            return jsonify({"error": f"Fallo en reserva de inventario: {error_msg}"}), respuesta_descuento.status_code
            
    except requests.exceptions.RequestException:
        logging.critical("Estrategia distribuida fallida: El inventario quedó completamente offline.")
        return jsonify({"error": "Inventario fuera de línea tras agotar reintentos catastróficos."}), 503

    # 3. Registrar el pedido en la base de datos local
    try:
        with obtener_conexion_db() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO pedidos (usuario_id, producto_id, cantidad, total, estado)
                    VALUES (%s, %s, %s, %s, 'PROCESADO') RETURNING id;
                """, (usuario_id, producto_id, cantidad, total_calculado))
                pedido_id = cursor.fetchone()[0]
            conexion.commit()
            logging.info(f"Pedido ID {pedido_id} persistido de forma atómica en db_orders.")
    except Exception as e:
        logging.error(f"Fallo crítico al escribir en base de datos local: {str(e)}")
        return jsonify({"error": "Error interno al procesar el almacenamiento de la orden"}), 500

    # 4. Comunicar al servicio de logística (Manejo con gracia de fallas de terceros)
    try:
        url_delivery = "http://delivery-service:5004/envios"
        respuesta_delivery = requests.post(url_delivery, json={"pedido_id": pedido_id}, headers=headers_internos, timeout=3)
        
        if respuesta_delivery.status_code == 201:
            datos_envio = respuesta_delivery.json()
            return jsonify({
                "pedido_id": pedido_id,
                "estado": "PROCESADO",
                "total": total_calculado,
                "logistica": {
                    "envio_id": datos_envio.get("envio_id"),
                    "repartidor": datos_envio.get("repartidor"),
                    "estado": datos_envio.get("estado_logistica")
                },
                "mensaje": "Pedido creado y pinguino repartidor asignado correctamente."
            }), 201
            
        else:
            logging.warning(f"Logística devolvió un código inesperado: {respuesta_delivery.status_code}") # Logueo específico para respuestas inesperadas del servicio de logística
            
    except requests.exceptions.RequestException: 
        logging.error(f"Servicio 'delivery-service' fuera de línea.(HTTP 202).") # Logueo específico para casos donde el servicio de logística no responde
        
    #El pedido se guardó pero la entrega se procesará de forma asíncrona posterior
    return jsonify({
        "pedido_id": pedido_id,
        "estado": "PROCESADO_PENDIENTE_LOGISTICA",
        "total": total_calculado,
        "mensaje": "Pedido registrado pero el camión de hielo no responde. Reintentando internamente."
    }), 202

# Endpoint para listar todos los pedidos, con validación de autenticación y manejo robusto de errores
@orders_blueprint.route('/pedidos', methods=['GET']) # Decorador para validar el token JWT y extraer el contexto del usuario
@requerir_token_autenticado # Decorador para validar el token JWT y extraer el contexto del usuario
def listar_todos_los_pedidos(usuario_contexto): # El contexto del usuario se inyecta automáticamente por el decorador.
    try:
        with obtener_conexion_db() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id, usuario_id, producto_id, cantidad, estado FROM pedidos ORDER BY id ASC;")
                pedidos = cursor.fetchall()
                
        lista_pedidos = [{
            "id": p[0],
            "usuario_id": p[1],
            "producto_id": p[2],
            "cantidad": p[3],
            "estado": p[4]
        } for p in pedidos] # Refactorización limpia usando listas de comprensión (Clean Code)
        
        return jsonify(lista_pedidos), 200
    except Exception as e:
        logging.error(f"Fallo en GET /pedidos: {str(e)}")
        return jsonify({"error": f"Error al consultar pedidos: {str(e)}"}), 500
    
# Endpoint para eliminar un pedido por ID, con validación de autenticación y manejo robusto de errores
@orders_blueprint.route('/pedidos/<int:pedido_id>', methods=['DELETE'])
@requerir_token_autenticado
def eliminar_pedido(pedido_id, usuario_contexto):
    try:
        with obtener_conexion_db() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id FROM pedidos WHERE id = %s;", (pedido_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Pedido no encontrado"}), 404
                    
                cursor.execute("DELETE FROM pedidos WHERE id = %s;", (pedido_id,))
            conexion.commit()
            
        logging.info(f"Pedido ID {pedido_id} purgado físicamente por solicitud del cliente.")
        return jsonify({"mensaje": f"Pedido ID {pedido_id} eliminado correctamente de la base de datos"}), 200
    except Exception as e:
        logging.error(f"Fallo en DELETE /pedidos/{pedido_id}: {str(e)}")
        return jsonify({"error": f"Error al eliminar el pedido: {str(e)}"}), 500