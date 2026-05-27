import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

JWT_SECRET = os.getenv("JWT_SECRET", "pinguino_secreto_super_seguro")
JWT_ALGORITHM = "HS256"

def generar_token_jwt(usuario_id: int, rol: str) -> str:
    """Genera un token JWT con expiración de 2 horas."""
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
        "iat": datetime.now(timezone.utc),
        "sub": usuario_id,
        "rol": rol
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
    return decorador_funcion