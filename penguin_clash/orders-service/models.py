import psycopg2 #Se importa la librería psycopg2 para conectarse a la base de datos PostgreSQL
import time # Se importa la librería time para implementar una espera en caso de que la base de datos no esté disponible al iniciar el servicio
from config import DATABASE_URL # Se importa la variable DATABASE_URL desde el archivo de configuración, que contiene la URL de conexión a la base de datos PostgreSQL

def obtener_conexion_db(): # Función para obtener una conexión a la base de datos PostgreSQL, con un mecanismo de reintento en caso de que la base de datos no esté disponible al iniciar el servicio
    while True:
        try:
            return psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError:
            print("Esperando a la base de datos db-orders...")
            time.sleep(2)

def inicializar_tabla_pedidos():# Función para inicializar la tabla de pedidos en la base de datos PostgreSQL, creando la tabla si no existe
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