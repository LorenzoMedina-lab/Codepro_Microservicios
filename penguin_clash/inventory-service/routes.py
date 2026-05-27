from flask import Blueprint, request, jsonify # Blueprint para organizar las rutas del microservicio de inventario
from models import obtener_conexion_db # Función para obtener una conexión a la base de datos PostgreSQL
from auth_shared import requerir_token_autenticado # Decorator para proteger endpoints que requieren autenticación JWT

inventory_blueprint = Blueprint('inventory', __name__)

@inventory_blueprint.route('/productos/<int:producto_id>', methods=['GET']) # Endpoint para obtener el detalle de un producto específico por su ID
def obtener_detalle_producto(producto_id): # Consulta a la base de datos para obtener el detalle del producto solicitado
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, nombre, stock, precio FROM productos WHERE id = %s;", (producto_id,))
            producto = cursor.fetchone()
            
    if not producto:
        return jsonify({"error": "Producto no encontrado en el glaciar"}), 404 # Si el producto no existe, se devuelve un error 404 con un mensaje adecuado
        
    return jsonify({"id": producto[0], "nombre": producto[1], "stock": producto[2], "precio": float(producto[3])}), 200

@inventory_blueprint.route('/productos/<int:producto_id>/descontar', methods=['POST'])
@requerir_token_autenticado
def descontar_stock_existente(producto_id, usuario_contexto):
    datos = request.get_json() or {}
    cantidad_a_descontar = datos.get('cantidad', 0)
    
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT stock FROM productos WHERE id = %s FOR UPDATE;", (producto_id,))
            resultado = cursor.fetchone()
            
            if not resultado:
                return jsonify({"error": "Producto no existe"}), 404
                
            stock_actual = resultado[0]
            if stock_actual < cantidad_a_descontar:
                return jsonify({"error": "Stock insuficiente para la operacion"}), 400
                
            nuevo_stock = stock_actual - cantidad_a_descontar
            cursor.execute("UPDATE productos SET stock = %s WHERE id = %s;", (nuevo_stock, producto_id))
        conexion.commit()
        
    return jsonify({"mensaje": "Stock descontado con exito", "nuevo_stock": nuevo_stock}), 200