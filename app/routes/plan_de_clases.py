from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query

from app.core.permissions import require_asignacion_access, require_plan_de_clases_access
from app.dependencies import get_current_active_admin, get_current_user
from app.controllers.plan_de_clases_controller import (
    actualizar_revision_plan_controller,
    crear_observacion_plan_controller,
    crear_plan_de_clases_controller,
    eliminar_imagen_plan_admin_controller,
    listar_observaciones_plan_controller,
    listar_planes_admin_controller,
    marcar_observacion_vista_controller,
    obtener_notificaciones_planeadores_controller,
    obtener_plan_admin_controller,
    obtener_plan_del_dia_controller,
    obtener_planes_por_asignacion_controller,
)
from app.schemas.plan_de_clases import (
    PlanDeClasesCreate,
    PlanObservacionCreate,
    PlanRevisionUpdate,
)
from datetime import date

router = APIRouter(tags=["Plan De Clases"])


@router.get("/notificaciones/planeadores")
def obtener_notificaciones_planeadores(
    limit: int = Query(8, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("rol") not in {"admin", "profesor"}:
        raise HTTPException(status_code=403, detail="No autorizado")
    return obtener_notificaciones_planeadores_controller(current_user, limit=limit)


@router.post("/plan-de-clases")
def crear_plan_de_clases(
    asignacion_id: int = Form(...),
    version_esperada: Optional[int] = Form(None),
    periodo: int = Form(1),
    unidad: str = Form(""),
    proposito: str = Form(""),
    clase: str = Form(""),
    estandar: str = Form(""),
    dba: str = Form(""),
    competencias: str = Form(""),
    actividad_casa: str = Form(""),
    tema: str = Form(""),
    fecha: str = Form(...),
    imagen1: UploadFile = File(None),
    imagen2: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    require_asignacion_access(asignacion_id, current_user, detail="No tienes permisos para esta asignación")
    try:
        plan = PlanDeClasesCreate(
            asignacion_id=asignacion_id,
            version_esperada=version_esperada,
            periodo=periodo,
            unidad=unidad,
            proposito=proposito,
            clase=clase,
            estandar=estandar,
            dba=dba,
            competencias=competencias,
            actividad_casa=actividad_casa,
            tema=tema,
            fecha=date.fromisoformat(fecha),
        )
        result = crear_plan_de_clases_controller(plan, imagen1, imagen2, usuario=current_user)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/plan-de-clases/{asignacion_id}")
def obtener_planes_por_asignacion(
    asignacion_id: int,
    fecha: Optional[date] = None,
    limit: Optional[int] = Query(None, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    require_asignacion_access(asignacion_id, current_user, detail="No tienes permisos para esta asignación")
    try:
        if fecha:
            return obtener_plan_del_dia_controller(asignacion_id, fecha)
        planes = obtener_planes_por_asignacion_controller(
            asignacion_id,
            limit=limit,
            offset=offset,
        )
        return planes
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/plan-de-clases/{plan_id}/imagen")
def eliminar_imagen_plan_profesor(
    plan_id: int,
    slot: str = Query(..., pattern="^(imagen1|imagen2)$"),
    current_user: dict = Depends(get_current_user),
):
    require_plan_de_clases_access(plan_id, current_user, detail="No tienes permisos para este plan")
    try:
        return eliminar_imagen_plan_admin_controller(
            plan_id,
            slot,
            reiniciar_revision=True,
            usuario=current_user,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo eliminar la imagen")


@router.get("/admin/plan-de-clases", dependencies=[Depends(get_current_active_admin)])
def listar_planes_admin(
    profesor_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    busqueda: Optional[str] = None,
    estado_revision: Optional[
        Literal["pendiente", "visto", "con_observaciones", "revisado"]
    ] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Sin `anio_lectivo_id`, los planes del año activo."""
    try:
        return listar_planes_admin_controller(
            profesor_id=profesor_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            busqueda=busqueda,
            estado_revision=estado_revision,
            limit=limit,
            offset=offset,
            anio_lectivo_id=anio_lectivo_id,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudieron cargar los planes de clases")


@router.get(
    "/admin/plan-de-clases/{plan_id}",
    dependencies=[Depends(get_current_active_admin)],
)
def obtener_plan_admin(plan_id: int):
    return obtener_plan_admin_controller(plan_id)


@router.patch("/admin/plan-de-clases/{plan_id}/revision")
def actualizar_revision_plan(
    plan_id: int,
    data: PlanRevisionUpdate,
    current_user: dict = Depends(get_current_active_admin),
):
    return actualizar_revision_plan_controller(plan_id, data, current_user["id"])


@router.post("/admin/plan-de-clases/{plan_id}/observaciones")
def crear_observacion_plan(
    plan_id: int,
    data: PlanObservacionCreate,
    current_user: dict = Depends(get_current_active_admin),
):
    return crear_observacion_plan_controller(plan_id, data, current_user["id"])


@router.get("/plan-de-clases/{plan_id}/observaciones")
def listar_observaciones_plan(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
):
    require_plan_de_clases_access(
        plan_id,
        current_user,
        detail="No tienes permisos para este plan",
    )
    return listar_observaciones_plan_controller(plan_id)


@router.patch("/plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista")
def marcar_observacion_vista(
    plan_id: int,
    observacion_id: int,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=403, detail="Accion exclusiva para profesores")
    require_plan_de_clases_access(
        plan_id,
        current_user,
        detail="No tienes permisos para este plan",
    )
    return marcar_observacion_vista_controller(plan_id, observacion_id, usuario=current_user)


@router.delete("/admin/plan-de-clases/{plan_id}/imagen")
def eliminar_imagen_plan_admin(
    plan_id: int,
    slot: str = Query(..., pattern="^(imagen1|imagen2)$"),
    # Año lectivo, paso 3.7: la guardia necesita saber quien guarda. La misma
    # proteccion de admin que antes iba en el decorador, ahora como parametro,
    # como en la revision y las observaciones del admin.
    current_user: dict = Depends(get_current_active_admin),
):
    try:
        return eliminar_imagen_plan_admin_controller(plan_id, slot, usuario=current_user)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo eliminar la imagen")
