import psycopg2
import os
from dotenv import load_dotenv
from app.globals import tenant_schema_var

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
     # Leemos el esquema dinámico de la petición actual (por defecto tenant_colegio_1 si no existe)
     tenant_schema = tenant_schema_var.get()
     
     conn = psycopg2.connect(DATABASE_URL)
     with conn.cursor() as cur:
          cur.execute(f'SET search_path TO "{tenant_schema}";')
     return conn
