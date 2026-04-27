from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.pago import PagoCreate

# 👇 Importamos controllers
from app.controllers.pagos_controller import (
    registrar_pago_controller,
    historial_pagos_controller
)

router = APIRouter(tags=["Pagos"], dependencies=[Depends(get_current_user)])


# 💰 Registrar pago
@router.post("/pagos")
def registrar_pago(pago: PagoCreate):

    pago_id = registrar_pago_controller(pago)

    return {
        "mensaje": "Pago registrado correctamente",
        "pago_id": pago_id
    }


# 📄 Ver historial
@router.get("/pagos/{estudiante_id}")
def historial_pagos(estudiante_id: int):

    return historial_pagos_controller(estudiante_id)
