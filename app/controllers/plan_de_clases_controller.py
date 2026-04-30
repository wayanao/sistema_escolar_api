from app.schemas.plan_de_clases import PlanDeClasesCreate
from app.globals import tenant_schema_var
from app.services.plan_de_clases_service import (
    guardar_plan,
    listar_reportes_admin,
    obtener_historial_asignacion,
    obtener_plan_del_dia,
)
import os
from datetime import datetime

def obtener_directorio_archivos():
    tenant = tenant_schema_var.get()
    directorio = f"uploads/{tenant}/plan_de_clases"
    os.makedirs(directorio, exist_ok=True)
    return directorio

def crear_plan_de_clases_controller(plan: PlanDeClasesCreate, imagen1=None, imagen2=None):
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

    return guardar_plan(plan, imagen1_path, imagen2_path)

def obtener_planes_por_asignacion_controller(asignacion_id):
    return obtener_historial_asignacion(asignacion_id)


def obtener_plan_del_dia_controller(asignacion_id, fecha):
    return obtener_plan_del_dia(asignacion_id, fecha)


def listar_planes_admin_controller(**filtros):
    return listar_reportes_admin(**filtros)
