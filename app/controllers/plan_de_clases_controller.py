from app.database import get_connection
from app.schemas.plan_de_clases import PlanDeClasesCreate, PlanDeClasesResponse
from app.globals import tenant_schema_var
import os
from datetime import datetime

def obtener_directorio_archivos():
    tenant = tenant_schema_var.get()
    directorio = f"uploads/{tenant}/plan_de_clases"
    os.makedirs(directorio, exist_ok=True)
    return directorio

def crear_plan_de_clases_controller(plan: PlanDeClasesCreate, imagen1=None, imagen2=None):
    conn = get_connection()
    cursor = conn.cursor()

    upload_dir = obtener_directorio_archivos()

    imagen1_path = None
    imagen2_path = None

    if imagen1:
        imagen1_path = f"{upload_dir}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{imagen1.filename}"
        with open(imagen1_path, "wb") as f:
            f.write(imagen1.file.read())

    if imagen2:
        imagen2_path = f"{upload_dir}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{imagen2.filename}"
        with open(imagen2_path, "wb") as f:
            f.write(imagen2.file.read())

    cursor.execute("""
        INSERT INTO plan_de_clases (asignacion_id, unidad, proposito, estandar, dba, competencias, tema, fecha, imagen1, imagen2)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        plan.asignacion_id,
        plan.unidad,
        plan.proposito,
        plan.estandar,
        plan.dba,
        plan.competencias,
        plan.tema,
        plan.fecha,
        imagen1_path,
        imagen2_path
    ))

    plan_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "mensaje": "Plan de clases creado",
        "id": plan_id
    }

def obtener_planes_por_asignacion_controller(asignacion_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, asignacion_id, unidad, proposito, estandar, dba, competencias, tema, fecha, imagen1, imagen2
        FROM plan_de_clases
        WHERE asignacion_id = %s
        ORDER BY fecha DESC
    """, (asignacion_id,))

    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    planes = []
    for row in resultados:
        planes.append({
            "id": row[0],
            "asignacion_id": row[1],
            "unidad": row[2],
            "proposito": row[3],
            "estandar": row[4],
            "dba": row[5],
            "competencias": row[6],
            "tema": row[7],
            "fecha": row[8],
            "imagen1": row[9],
            "imagen2": row[10]
        })

    return planes