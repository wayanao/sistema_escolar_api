from app.schemas.plan_de_clases import PlanDeClasesCreate
from app.globals import tenant_schema_var
from app.services.plan_de_clases_service import (
    eliminar_imagen_plan_admin,
    guardar_plan,
    listar_reportes_admin,
    obtener_historial_asignacion,
    obtener_plan_del_dia,
)
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, status

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

def obtener_directorio_archivos():
    tenant = tenant_schema_var.get()
    directorio = f"uploads/{tenant}/plan_de_clases"
    os.makedirs(directorio, exist_ok=True)
    return directorio


def guardar_imagen_plan(upload_dir, imagen):
    if not imagen:
        return None

    if imagen.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de imagen no permitido"
        )

    ext = Path(imagen.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension de imagen no permitida"
        )

    contenido = imagen.file.read()
    if len(contenido) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Imagen demasiado grande (max {MAX_IMAGE_BYTES // (1024 * 1024)}MB)"
        )

    destino = Path(upload_dir) / f"{uuid.uuid4().hex}{ext}"
    destino.write_bytes(contenido)
    return destino.as_posix()

def crear_plan_de_clases_controller(plan: PlanDeClasesCreate, imagen1=None, imagen2=None):
    upload_dir = obtener_directorio_archivos()

    imagen1_path = guardar_imagen_plan(upload_dir, imagen1)
    imagen2_path = guardar_imagen_plan(upload_dir, imagen2)

    return guardar_plan(plan, imagen1_path, imagen2_path)

def obtener_planes_por_asignacion_controller(asignacion_id):
    return obtener_historial_asignacion(asignacion_id)


def obtener_plan_del_dia_controller(asignacion_id, fecha):
    return obtener_plan_del_dia(asignacion_id, fecha)


def listar_planes_admin_controller(**filtros):
    return listar_reportes_admin(**filtros)


def eliminar_imagen_plan_admin_controller(plan_id, slot):
    path = eliminar_imagen_plan_admin(plan_id, slot)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan de clases no encontrado")

    if path:
        uploads_dir = Path("uploads").resolve()
        file_path = Path(str(path).replace("\\", "/")).resolve()
        try:
            file_path.relative_to(uploads_dir)
        except ValueError:
            file_path = None

        if file_path and file_path.is_file():
            file_path.unlink()

    return {"mensaje": "Imagen eliminada correctamente"}
