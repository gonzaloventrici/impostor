import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Crea y devuelve una conexión a la base de datos usando variables de entorno.

    Requiere un archivo .env (ver .env.example) con:
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
        )
        return connection
    except mysql.connector.Error as err:
        raise ConnectionError(f"Error de conexión a la base de datos: {err}") from err
