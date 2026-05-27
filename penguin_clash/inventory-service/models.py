import psycopg2
import time
from config import DATABASE_URL

def obtener_conexion_db():
    while True:
        try:
            return psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError:
            print("Esperando a la base de datos db-inventory...")
            time.sleep(2)

def inicializar_tabla_inventario():
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    stock INT NOT NULL,
                    precio NUMERIC(10, 2) NOT NULL
                );
            """)
            cursor.execute("SELECT id FROM productos WHERE nombre = 'Cubo de Hielo Glacial';")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO productos (nombre, stock, precio) VALUES ('Cubo de Hielo Glacial', 150, 4.50);")
                cursor.execute("INSERT INTO productos (nombre, stock, precio) VALUES ('Bloque de Hielo Iceberg', 20, 25.00);")
        conexion.commit()