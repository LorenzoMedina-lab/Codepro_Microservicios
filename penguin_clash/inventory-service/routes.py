from flask import Blueprint, request, jsonify # Blueprint para organizar las rutas del microservicio de inventario
from models import obtener_conexion_db # Función para obtener una conexión a la base de datos PostgreSQL
from auth_shared import requerir_token_autenticado # Decorator para proteger endpoints que requieren autenticación JWT

inventory_blueprint = Blueprint('inventory', __name__)

# Endpoint para obtener el detalle de un producto específico por su ID
@inventory_blueprint.route('/productos/<int:producto_id>', methods=['GET'])
def obtener_detalle_producto(producto_id): # Consulta a la base de datos para obtener el detalle del producto solicitado
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, nombre, stock, precio FROM productos WHERE id = %s;", (producto_id,))
            producto = cursor.fetchone()
            
    if not producto:
        return jsonify({"error": "Producto no encontrado en el glaciar"}), 404 # Si el producto no existe, se devuelve un error 404 con un mensaje adecuado
        
    return jsonify({"id": producto[0], "nombre": producto[1], "stock": producto[2], "precio": float(producto[3])}), 200

# Endpoint para descontar stock de un producto específico, protegido por autenticación JWT.
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

# Endpoint para listar todos los productos disponibles en el inventario, ordenados por ID de forma ascendente
@inventory_blueprint.route('/productos', methods=['GET'])
def listar_todos_los_productos():
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, nombre, stock, precio FROM productos ORDER BY id ASC;")
            productos = cursor.fetchall()
            
    lista_productos = []
    for p in productos:
        lista_productos.append({
            "id": p[0],
            "nombre": p[1],
            "stock": p[2],
            "precio": float(p[3]) # Casteo necesario para evitar error de serialización de UUID/Decimal en Postgres
        })
        
    return jsonify(lista_productos), 200

# Endpoint para agregar un nuevo producto al inventario, protegido por autenticación JWT.
@inventory_blueprint.route('/productos', methods=['POST'])
@requerir_token_autenticado  # Protegido para que solo usuarios logueados metan stock
def agregar_nuevo_producto(usuario_contexto):
    datos = request.get_json() or {}
    nombre = datos.get('nombre')
    stock = datos.get('stock', 0)
    precio = datos.get('precio', 0.0)
    
    if not nombre:
        return jsonify({"error": "El campo 'nombre' es obligatorio"}), 400
        
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO productos (nombre, stock, precio) 
                VALUES (%s, %s, %s) RETURNING id;
            """, (nombre, stock, precio))
            nuevo_id = cursor.fetchone()[0]
        conexion.commit()
        
    return jsonify({
        "mensaje": "Producto agregado al inventario del glaciar",
        "producto_id": nuevo_id
    }), 201

# Endpoint para actualizar el nombre o precio de un producto específico, protegido por autenticación JWT.
@inventory_blueprint.route('/productos/<int:producto_id>', methods=['PUT'])
@requerir_token_autenticado  # Solo usuarios autenticados pueden modificar
def actualizar_producto(producto_id, usuario_contexto):
    datos = request.get_json() or {}
    nuevo_nombre = datos.get('nombre')
    nuevo_precio = datos.get('precio')
    
    if not nuevo_nombre and nuevo_precio is None:
        return jsonify({"error": "Se requiere al menos el campo 'nombre' o 'precio' para actualizar"}), 400
        
    try:
        with obtener_conexion_db() as conexion:
            with conexion.cursor() as cursor:
                # Primero verificamos si existe
                cursor.execute("SELECT id FROM productos WHERE id = %s;", (producto_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Producto no encontrado"}), 404
                
                # Dinámicamente actualizamos lo que venga en el JSON
                if nuevo_nombre:
                    cursor.execute("UPDATE productos SET nombre = %s WHERE id = %s;", (nuevo_nombre, producto_id))
                if nuevo_precio is not None:
                    cursor.execute("UPDATE productos SET precio = %s WHERE id = %s;", (nuevo_precio, producto_id))
            conexion.commit()
            
        return jsonify({"mensaje": f"Producto ID {producto_id} actualizado con éxito"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al actualizar producto: {str(e)}"}), 500