# config.py
import os

# Recupera la cadena de conexión de PostgreSQL inyectada por Docker
# Si no encuentra la variable, usa un string vacío por seguridad
DATABASE_URL = os.getenv("DATABASE_URL", "")