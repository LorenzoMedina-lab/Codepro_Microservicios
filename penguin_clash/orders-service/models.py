import psycopg2
import time
from config import DATABASE_URL

def obtener_conexion_db():
    while True:
        try:
            return psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError:
            print("Esperando a la base de datos db-orders...")
            time.sleep(2)

def inicializar_tabla_pedidos():
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id SERIAL PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    producto_id INT NOT NULL,
                    cantidad INT NOT NULL,
                    total NUMERIC(10,2) NOT NULL,
                    estado VARCHAR(30) NOT NULL
                );
            """)
        conexion.commit()