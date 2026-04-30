import os
import getpass
import re
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

from app.security import get_password_hash

# Cargar variables de entorno del proyecto.
load_dotenv(Path(__file__).resolve().parent / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")
TEMPLATE_SCHEMA = os.getenv("DEFAULT_TENANT_SCHEMA", "tenant_colegio_1")
TENANT_CODE_PATTERN = re.compile(r"^[a-z0-9_]{3,50}$")

# Este es el molde exacto de todas tus tablas actuales.
# Se ejecutará dentro de la bóveda del nuevo colegio.
ESQUEMA_BASE_SQL = """
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE cursos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    matricula NUMERIC,
    mensualidad NUMERIC,
    meses INTEGER
);

CREATE TABLE materias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT
);

CREATE TABLE profesor (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    documento_identidad VARCHAR(50),
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(50),
    password VARCHAR(255) NOT NULL
);

CREATE TABLE estudiantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    documento_identidad VARCHAR(50),
    curso_id INTEGER REFERENCES cursos(id),
    estado VARCHAR(50) DEFAULT 'Activo',
    anio_escolar INTEGER,
    fecha_nacimiento DATE,
    descuento_matricula NUMERIC DEFAULT 0,
    descuento_mensualidad NUMERIC DEFAULT 0,
    condicion_diagnostico VARCHAR(255)
);

CREATE TABLE asignaciones (
    id SERIAL PRIMARY KEY,
    curso_id INTEGER REFERENCES cursos(id),
    materia_id INTEGER REFERENCES materias(id),
    profesor_id INTEGER REFERENCES profesor(id)
);

CREATE TABLE plan_de_clases (
    id SERIAL PRIMARY KEY,
    asignacion_id INTEGER REFERENCES asignaciones(id),
    periodo INTEGER DEFAULT 1,
    unidad VARCHAR(255),
    proposito TEXT,
    clase TEXT DEFAULT '',
    estandar TEXT,
    dba TEXT,
    competencias TEXT,
    actividad_casa TEXT DEFAULT '',
    tema VARCHAR(255),
    fecha DATE,
    imagen1 VARCHAR(255),
    imagen2 VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plan_de_clases_asignacion_fecha ON plan_de_clases(asignacion_id, fecha);
CREATE INDEX idx_plan_de_clases_fecha ON plan_de_clases(fecha);

CREATE TABLE boletin_cabecera (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER REFERENCES estudiantes(id),
    asignacion_id INTEGER REFERENCES asignaciones(id),
    periodo INTEGER,
    definitiva NUMERIC,
    UNIQUE(estudiante_id, asignacion_id, periodo)
);

CREATE TABLE boletin_detalles (
    id SERIAL PRIMARY KEY,
    boletin_id INTEGER REFERENCES boletin_cabecera(id) ON DELETE CASCADE,
    nota NUMERIC,
    observacion TEXT
);

CREATE TABLE tipos_de_pagos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    valor NUMERIC NOT NULL
);

CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER REFERENCES estudiantes(id),
    tipo_pago VARCHAR(100),
    monto NUMERIC,
    fecha_pago DATE,
    estado VARCHAR(50),
    mes VARCHAR(50),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT
);

-- (Si faltan tablas como inventario/egresos, se pueden agregar fácilmente aquí)
"""

def registrar_nuevo_colegio():
    print("\n" + "="*50)
    print(" 🏫 ASISTENTE DE CREACIÓN DE NUEVOS CLIENTES (SAAS) ")
    print("="*50 + "\n")

    nombre_colegio = input("1. Nombre completo del Colegio: ")
    codigo_colegio = input("2. Código de Ingreso (ej. sanpedro): ").lower().replace(" ", "_")
    admin_nombre = input("3. Nombre del Administrador Director: ")
    admin_email = input("4. Correo de este administrador: ")
    admin_pass = getpass.getpass("5. Contraseña para este administrador: ")

    if not TENANT_CODE_PATTERN.fullmatch(codigo_colegio):
        print("\n❌ Código inválido. Usa solo letras minúsculas, números o guion bajo. Mínimo 3 caracteres.")
        return

    esquema_nuevo = f"tenant_{codigo_colegio}"

    print(f"\n🚀 Preparando entorno para {nombre_colegio}...")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()

        # 1. Registrar Colegio Global
        cursor.execute("""
            INSERT INTO public.colegios (nombre, subdominio, esquema_db, estado)
            VALUES (%s, %s, %s, 'activo')
        """, (nombre_colegio, codigo_colegio, esquema_nuevo))

        # 2. Crear Bóveda Privada
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(esquema_nuevo)))
        cursor.execute(
            sql.SQL("SET search_path TO {}, public").format(sql.Identifier(esquema_nuevo))
        )

        # 3. Crear Tablas Estructurales
        print("📁 Creando bases de datos y relaciones...")
        cursor.execute("""
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = %(template_schema)s
    ) LOOP
        EXECUTE format(
            'CREATE TABLE %I.%I (LIKE %I.%I INCLUDING ALL)',
            %(target_schema)s, r.tablename,
            %(template_schema)s, r.tablename
        );
    END LOOP;
END $$;
""", {
            "target_schema": esquema_nuevo,
            "template_schema": TEMPLATE_SCHEMA,
        })

        # 4. Insertar Primer Administrador
        print("👤 Registrando cuenta de administrador...")
        
        # Corrección temporal para evitar error de passlib con versiones de bcrypt modernas
        # Generar hash de password de forma directa si passlib falla
        try:
            hashed_pass = get_password_hash(admin_pass)
        except Exception:
            import bcrypt
            hashed_pass = bcrypt.hashpw(admin_pass[:72].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, rol, password)
            VALUES (%s, %s, 'admin', %s)
        """, (admin_nombre, admin_email, hashed_pass))

        conn.commit()
        print("\n✅ ¡COLEGIO CREADO EXISTOSAMENTE!")
        print(f"El colegio '{nombre_colegio}' ya puede iniciar sesión.")
        print(f"👉 Su código de acceso es: {codigo_colegio}\n")

    except psycopg2.IntegrityError as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        print(f"\n❌ Error de Integridad: {e}")
        print("💡 Es probable que el código del colegio o el correo de este usuario ya estén registrados en la base de datos.")
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        print(f"\n❌ Ocurrió un error inesperado al conectar a PostgreSQL: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    registrar_nuevo_colegio()
