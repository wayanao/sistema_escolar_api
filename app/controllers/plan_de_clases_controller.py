from pathlib import Path
import uuid

from fastapi import HTTPException, status

from app.schemas.plan_de_clases import (
    PlanDeClasesCreate,
    PlanObservacionCreate,
    PlanRevisionUpdate,
)
from app.globals import tenant_schema_var
from app.services.plan_de_clases_service import (
    actualizar_revision,
    confirmar_observacion_vista,
    crear_observacion_plan,
    eliminar_imagen_plan_admin,
    guardar_plan,
    listar_planes_anio_anterior,
    listar_reportes_admin,
    obtener_observaciones_plan,
    obtener_notificaciones_planeadores,
    obtener_plan_admin,
    obtener_plan_anio_anterior,
    obtener_historial_asignacion,
    obtener_plan_del_dia,
)
from app.services.storage import delete_file, db_path_for_key, save_bytes

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
MAX_PDF_BYTES = 15 * 1024 * 1024
# Los cinco primeros bytes de todo PDF. Se verifica el contenido y no solo el
# nombre para que renombrar un archivo a .pdf no alcance para subirlo.
FIRMA_PDF = b"%PDF-"

# Año lectivo, fase 7 (paso 7.2): usar un plan del año pasado como base.
MENSAJE_PLAN_NO_ES_DEL_ANIO_ANTERIOR = "Ese plan no es del año pasado de esta clase."


def obtener_directorio_archivos():
    tenant = tenant_schema_var.get()
    return f"{tenant}/plan_de_clases"


def guardar_imagen_plan(upload_dir, imagen):
    """Guarda una evidencia del plan: imagen hasta 5MB o PDF hasta 15MB."""
    if not imagen:
        return None

    es_pdf = imagen.content_type in ALLOWED_PDF_TYPES
    if not es_pdf and imagen.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido. Use imagen o PDF"
        )

    extensiones = ALLOWED_PDF_EXTENSIONS if es_pdf else ALLOWED_EXTENSIONS
    ext = Path(imagen.filename or "").suffix.lower()
    if ext not in extensiones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension de archivo no permitida"
        )

    maximo = MAX_PDF_BYTES if es_pdf else MAX_IMAGE_BYTES
    contenido = imagen.file.read()
    if len(contenido) > maximo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo demasiado grande (max {maximo // (1024 * 1024)}MB)"
        )

    if es_pdf and not contenido.startswith(FIRMA_PDF):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es un PDF valido"
        )

    key = f"{upload_dir}/{uuid.uuid4().hex}{ext}"
    save_bytes(key, contenido, imagen.content_type)
    return db_path_for_key(key)


def crear_plan_de_clases_controller(
    plan: PlanDeClasesCreate, imagen1=None, imagen2=None, *, usuario
):
    upload_dir = obtener_directorio_archivos()
    imagenes_creadas = []

    try:
        imagen1_path = guardar_imagen_plan(upload_dir, imagen1)
        if imagen1_path:
            imagenes_creadas.append(imagen1_path)

        imagen2_path = guardar_imagen_plan(upload_dir, imagen2)
        if imagen2_path:
            imagenes_creadas.append(imagen2_path)

        resultado = guardar_plan(plan, imagen1_path, imagen2_path, usuario=usuario)
        if resultado.get("resultado") == "version_desactualizada":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "mensaje": (
                        "Este plan fue actualizado en otra pestaña o dispositivo. "
                        "Carga la versión más reciente antes de guardar."
                    ),
                    "version_actual": resultado.get("version_actual"),
                },
            )
        return resultado
    except Exception:
        for imagen_path in imagenes_creadas:
            delete_file(imagen_path)
        raise


def obtener_planes_por_asignacion_controller(asignacion_id, limit=None, offset=0):
    return obtener_historial_asignacion(
        asignacion_id,
        limit=limit,
        offset=offset,
    )


def obtener_plan_del_dia_controller(asignacion_id, fecha):
    return obtener_plan_del_dia(asignacion_id, fecha)


def listar_planes_admin_controller(**filtros):
    return listar_reportes_admin(**filtros)


def obtener_plan_admin_controller(plan_id):
    plan = obtener_plan_admin(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de clases no encontrado",
        )
    return plan


def listar_planes_anio_anterior_controller(asignacion_id, *, usuario):
    return listar_planes_anio_anterior(asignacion_id, usuario=usuario)


def obtener_plan_anio_anterior_controller(asignacion_id, plan_id, *, usuario):
    """El texto de un plan del año pasado; 403 si no es del origen de la clase.

    Un plan que no existe recibe el mismo 403: no se dice si existe en otra
    clase.
    """
    plan = obtener_plan_anio_anterior(asignacion_id, plan_id, usuario=usuario)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MENSAJE_PLAN_NO_ES_DEL_ANIO_ANTERIOR,
        )
    return plan


def _resolver_resultado_revision(resultado):
    if resultado["resultado"] == "no_encontrado":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de clases no encontrado",
        )
    if resultado["resultado"] == "version_desactualizada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "mensaje": "El plan fue actualizado. Recarga antes de continuar.",
                "version_actual": resultado["version_actual"],
            },
        )
    return resultado


def actualizar_revision_plan_controller(
    plan_id: int,
    data: PlanRevisionUpdate,
    admin_id: int,
):
    resultado = actualizar_revision(
        plan_id,
        data.estado,
        admin_id,
        data.version,
        comentario=data.comentario,
    )
    return _resolver_resultado_revision(resultado)


def crear_observacion_plan_controller(
    plan_id: int,
    data: PlanObservacionCreate,
    admin_id: int,
):
    resultado = crear_observacion_plan(
        plan_id,
        admin_id,
        data.version,
        data.observacion,
    )
    return _resolver_resultado_revision(resultado)


def listar_observaciones_plan_controller(plan_id):
    obtener_plan_admin_controller(plan_id)
    return obtener_observaciones_plan(plan_id)


def marcar_observacion_vista_controller(plan_id, observacion_id, *, usuario):
    resultado = confirmar_observacion_vista(plan_id, observacion_id, usuario=usuario)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Observacion no encontrada para este plan",
        )
    return resultado


def obtener_notificaciones_planeadores_controller(current_user, limit=8):
    return obtener_notificaciones_planeadores(current_user, limit=limit)


def eliminar_imagen_plan_admin_controller(plan_id, slot, reiniciar_revision=False, *, usuario):
    path = eliminar_imagen_plan_admin(
        plan_id,
        slot,
        reiniciar_revision=reiniciar_revision,
        usuario=usuario,
    )
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan de clases no encontrado")

    delete_file(path)

    return {"mensaje": "Imagen eliminada correctamente"}
