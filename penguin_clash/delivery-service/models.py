import psycopg2
import time
from config import DATABASE_URL

def obtener_conexion_db():
    while True:
        try:
            return psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError:
            print("Esperando a la base de datos db-delivery...")
            time.sleep(2)

def inicializar_tabla_envios():
    """Crea la tabla para gestionar la logística de los repartidores."""
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS envios (
                    id SERIAL PRIMARY KEY,
                    pedido_id INT UNIQUE NOT NULL,
                    repartidor_asignado VARCHAR(100) NOT NULL,
                    estado_envio VARCHAR(30) NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conexion.commit()