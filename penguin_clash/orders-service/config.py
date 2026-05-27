# config.py
import os

# Recupera la cadena de conexión de PostgreSQL local de este servicio
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Dirección del microservicio de inventario dentro de la red de Docker
# Apunta por defecto a la URL interna declarada en el compose
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:5002")