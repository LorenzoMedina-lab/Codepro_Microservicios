import os #Importa el módulo os para acceder a las variables de entorno.
import jwt #Importa la biblioteca PyJWT para generar y validar tokens JWT.
from datetime import datetime, timedelta, timezone #Importa clases para manejar fechas y tiempos, incluyendo zonas horarias.
from functools import wraps #Importa wraps para crear decoradores que preserven la firma original de las funciones decoradas.
from flask import request, jsonify #Importa request y jsonify de Flask para manejar solicitudes HTTP y respuestas JSON.

JWT_SECRET = os.getenv("JWT_SECRET", "pinguino_secreto_super_seguro") #Clave secreta para firmar los tokens JWT, obtenida de una variable de entorno o con un valor por defecto para desarrollo. En producción, esta clave debe ser segura y no compartida.
JWT_ALGORITHM = "HS256" #Algoritmo de firma para los tokens JWT, utilizando HMAC con SHA-256.

def generar_token_jwt(usuario_id: int, rol: str) -> str: #Agrega el rol al token para futuras autorizaciones basadas en roles
    """Genera un token JWT con expiración de 2 horas."""
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
        "iat": datetime.now(timezone.utc),
        "sub": usuario_id,
        "rol": rol
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM) #Agrega el rol al payload del token para futuras autorizaciones basadas en roles

def requerir_token_autenticado(funcion_original):
    """Decorator para proteger endpoints REST. Valida el Bearer token."""
    @wraps(funcion_original) #Preserva la firma original de la función decorada para que Flask pueda manejarla correctamente
    def decorador_funcion(*args, **kwargs):#Extrae el token del encabezado Authorization y lo valida. Si es válido, inyecta los datos del token en los kwargs del endpoint para que estén disponibles dentro de la función original.
        headers_autorizacion = request.headers.get("Authorization", None)
        
        if not headers_autorizacion: #Si no se proporciona el encabezado de autorización, responde con un error 401
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
            
        return funcion_original(*args, **kwargs) #Llama a la función original del endpoint con los datos del token inyectados en los kwargs
    return decorador_funcion