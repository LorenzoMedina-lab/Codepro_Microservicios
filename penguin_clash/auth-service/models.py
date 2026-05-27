import psycopg2
import time
from config import DATABASE_URL

def obtener_conexion_db():
    # Intenta conectar en bucle hasta que PostgreSQL acepte peticiones
    while True:
        try:
            return psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError:
            print("Esperando a la base de datos db-auth...")
            time.sleep(2)

def inicializar_tabla_usuarios():
    """Crea la tabla si no existe e inserta un usuario semilla para pruebas."""
    with obtener_conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    rol VARCHAR(20) NOT NULL
                );
            """)
            # Insertar pingüino administrador de prueba si no existe
            cursor.execute("SELECT id FROM usuarios WHERE username = 'admin_pinguino';")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO usuarios (username, password, rol) 
                    VALUES ('admin_pinguino', 'pescado123', 'admin');
                """)
        conexion.commit()