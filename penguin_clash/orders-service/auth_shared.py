import os # Agregado para manejar variables de entorno, como el secreto para JWT.
import jwt # Agregado para manejar la generación y validación de tokens JWT. Asegúrate de tener la biblioteca PyJWT instalada (pip install PyJWT).
from datetime import datetime, timedelta, timezone # Agregado para manejar fechas y horas, especialmente para establecer la expiración de los tokens JWT.
from functools import wraps # Agregado para crear decoradores, como el decorador de autenticación que se utiliza para proteger los endpoints REST.
from flask import request, jsonify # Agregado para manejar las solicitudes HTTP y las respuestas JSON en los endpoints REST.

JWT_SECRET = os.environ.get("JWT_SECRET") # Es importante que JWT_SECRET se defina en las variables de entorno para garantizar la seguridad de los tokens JWT.
JWT_ALGORITHM = "HS256" # Algoritmo de firma para los tokens JWT. HS256 es un algoritmo de firma simétrica que utiliza el secreto definido en JWT_SECRET para firmar y verificar los tokens.

def generar_token_jwt(usuario_id: int, rol: str) -> str: # Función para generar un token JWT con la información del usuario (ID y rol) y una expiración de 2 horas.
    """Genera un token JWT con expiración de 2 horas."""
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(hours=2), # Establece la expiración del token a 2 horas a partir del momento de su creación.
        "iat": datetime.now(timezone.utc), # Establece la fecha de emisión del token al momento actual.
        "sub": usuario_id, # El "sub" (subject) del token se establece como el ID del usuario, lo que permite identificar al usuario asociado con el token.
        "rol": rol # Agrega el rol del usuario al payload del token, lo que puede ser útil para implementar control de acceso basado en roles en los endpoints protegidos.
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def requerir_token_autenticado(funcion_original):
    """Decorator para proteger endpoints REST. Valida el Bearer token."""
    @wraps(funcion_original)
    def decorador_funcion(*args, **kwargs):
        headers_autorizacion = request.headers.get("Authorization", None)
        
        if not headers_autorizacion:
            return jsonify({"error": "Falta el encabezado de autorizacion"}), 401
            
        try:
            # Espera formato: "Bearer <token>"
            tipo_token, token = headers_autorizacion.split(" ")
            if tipo_token.lower() != "bearer":
                return jsonify({"error": "Tipo de token invalido, debe ser Bearer"}), 401
                
            datos_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            # Inyectamos los datos del token en los kwargs del endpoint
            kwargs['usuario_contexto'] = datos_token
            
        except (ValueError, jwt.ExpiredSignatureError, jwt.InvalidTokenError) as error_jwt:
            return jsonify({"error": f"Token invalido o expirado: {str(error_jwt)}"}), 401
            
        return funcion_original(*args, **kwargs)
    return decorador_funcion # Decorator para proteger endpoints REST. Valida el Bearer token.