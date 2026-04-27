from fastapi import APIRouter, HTTPException
from app.schemas.boletin import BoletinCreate
from app.controllers.boletin_controller import guardar_boletin_controller, obtener_notas_planilla_controller, obtener_boletin_admin_controller

router = APIRouter(prefix="/boletines", tags=["boletines"])

@router.post("/guardar")
def guardar_boletin(boletin: BoletinCreate):
    try:
        resultado = guardar_boletin_controller(boletin)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/referencia/{asignacion_id}/{periodo}")
def obtener_notas_referencia(asignacion_id: int, periodo: int):
    try:
        notas = obtener_notas_planilla_controller(asignacion_id, periodo)
        return notas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/admin/generar/{estudiante_id}/{periodo}")
def generar_boletin_admin(estudiante_id: int, periodo: int):
    try:
        resultado = obtener_boletin_admin_controller(estudiante_id, periodo)
        if not resultado:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))