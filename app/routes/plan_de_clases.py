from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.dependencies import get_current_user
from app.controllers.plan_de_clases_controller import crear_plan_de_clases_controller, obtener_planes_por_asignacion_controller
from app.schemas.plan_de_clases import PlanDeClasesCreate
from datetime import date

router = APIRouter(tags=["Plan De Clases"], dependencies=[Depends(get_current_user)])

@router.post("/plan-de-clases")
async def crear_plan_de_clases(
    asignacion_id: int = Form(...),
    unidad: str = Form(...),
    proposito: str = Form(...),
    estandar: str = Form(...),
    dba: str = Form(...),
    competencias: str = Form(...),
    tema: str = Form(...),
    fecha: str = Form(...),
    imagen1: UploadFile = File(None),
    imagen2: UploadFile = File(None)
):
    try:
        plan = PlanDeClasesCreate(
            asignacion_id=asignacion_id,
            unidad=unidad,
            proposito=proposito,
            estandar=estandar,
            dba=dba,
            competencias=competencias,
            tema=tema,
            fecha=date.fromisoformat(fecha)
        )
        result = crear_plan_de_clases_controller(plan, imagen1, imagen2)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/plan-de-clases/{asignacion_id}")
async def obtener_planes_por_asignacion(asignacion_id: int):
    try:
        planes = obtener_planes_por_asignacion_controller(asignacion_id)
        return planes
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))