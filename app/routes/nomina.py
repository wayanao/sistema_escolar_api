from fastapi import APIRouter, Depends, HTTPException, Body
from app.controllers.nomina_controller import obtener_estado_cuenta_profesores, procesar_pago_nomina, obtener_historial_nomina
from app.schemas.nomina import NominaCreate

router = APIRouter()

@router.get("/empleados")
def get_estado_empleados():
    return obtener_estado_cuenta_profesores()

@router.get("/historial")
def get_historial():
    return obtener_historial_nomina()

@router.post("/pagar")
def post_pago_nomina(data: NominaCreate):
    try:
        resultado = procesar_pago_nomina(data)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar pago: {str(e)}")
