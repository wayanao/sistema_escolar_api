from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query

from app.dependencies import get_current_active_admin, get_current_user
from app.controllers.plan_de_clases_controller import (
    crear_plan_de_clases_controller,
    listar_planes_admin_controller,
    obtener_plan_del_dia_controller,
    obtener_planes_por_asignacion_controller,
)
from app.schemas.plan_de_clases import PlanDeClasesCreate
from datetime import date

router = APIRouter(tags=["Plan De Clases"])

@router.post("/plan-de-clases", dependencies=[Depends(get_current_user)])
async def crear_plan_de_clases(
    asignacion_id: int = Form(...),
    periodo: int = Form(1),
    unidad: str = Form(...),
    proposito: str = Form(...),
    clase: str = Form(...),
    estandar: str = Form(...),
    dba: str = Form(...),
    competencias: str = Form(...),
    actividad_casa: str = Form(...),
    tema: str = Form(...),
    fecha: str = Form(...),
    imagen1: UploadFile = File(None),
    imagen2: UploadFile = File(None)
):
    try:
        plan = PlanDeClasesCreate(
            asignacion_id=asignacion_id,
            periodo=periodo,
            unidad=unidad,
            proposito=proposito,
            clase=clase,
            estandar=estandar,
            dba=dba,
            competencias=competencias,
            actividad_casa=actividad_casa,
            tema=tema,
            fecha=date.fromisoformat(fecha)
        )
        result = crear_plan_de_clases_controller(plan, imagen1, imagen2)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/plan-de-clases/{asignacion_id}", dependencies=[Depends(get_current_user)])
async def obtener_planes_por_asignacion(asignacion_id: int, fecha: Optional[date] = None):
    try:
        if fecha:
            return obtener_plan_del_dia_controller(asignacion_id, fecha)
        planes = obtener_planes_por_asignacion_controller(asignacion_id)
        return planes
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/plan-de-clases", dependencies=[Depends(get_current_active_admin)])
async def listar_planes_admin(
    profesor_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    busqueda: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    try:
        return listar_planes_admin_controller(
            profesor_id=profesor_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            busqueda=busqueda,
            limit=limit,
            offset=offset,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudieron cargar los planes de clases")
