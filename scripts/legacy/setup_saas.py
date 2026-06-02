import psycopg2
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde la raiz del backend.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
DATABASE_URL = os.getenv("DATABASE_URL")

def migrar_a_saas():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False # Usar transacciones para estar seguros
        cursor = conn.cursor()

        print("🚀 Iniciando migración a Arquitectura SaaS (Multi-tenant)...")

        # 1. Crear la tabla principal de Colegios ("Tenants") en el esquema public
        print("🏢 Creando tabla 'colegios' central en el esquema 'public'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.colegios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                subdominio VARCHAR(100) UNIQUE NOT NULL,
                estado VARCHAR(50) DEFAULT 'activo',
                esquema_db VARCHAR(100) UNIQUE NOT NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Insertar el colegio actual como el Inquilino #1 (Tenant 1)
        print("📝 Registrando el colegio actual como 'Colegio Demo'...")
        cursor.execute("""
            INSERT INTO public.colegios (nombre, subdominio, esquema_db)
            VALUES ('Colegio Demo', 'demo', 'tenant_colegio_1')
            ON CONFLICT (subdominio) DO NOTHING;
        """)

        # 3. Crear el nuevo esquema para el primer colegio
        print("📁 Creando el nuevo esquema aislado 'tenant_colegio_1'...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS tenant_colegio_1;")

        # 4. Obtener todas las tablas actuales en 'public' (excepto la tabla de 'colegios')
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' AND tablename != 'colegios';
        """)
        tablas = cursor.fetchall()

        # 5. Mover cada tabla existente al nuevo esquema aislado
        if tablas:
            print(f"📦 Moviendo {len(tablas)} tablas de 'public' a 'tenant_colegio_1':")
            for tabla in tablas:
                nombre_tabla = tabla[0]
                print(f"   - Moviendo tabla: {nombre_tabla}")
                cursor.execute(f"ALTER TABLE public.{nombre_tabla} SET SCHEMA tenant_colegio_1;")
        else:
            print("📦 No se encontraron tablas adicionales en 'public' o ya fueron movidas.")

        # Confirmar todos los cambios en bloque (Transacción)
        conn.commit()
        print("\n✅ ¡Migración de Base de Datos completada con éxito!")
        print("🔐 Ahora los datos de tu colegio están aislados en su propio esquema.")

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback() # Si algo falla, revertimos todo para no romper la base de datos
        print(f"\n❌ Error durante la migración: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    migrar_a_saas()
