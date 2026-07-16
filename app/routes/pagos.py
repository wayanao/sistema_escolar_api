from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies import get_current_active_admin
from app.schemas.pago import PagoAdelantadoCreate, PagoAnular, PagoCreate

# 👇 Importamos controllers
from app.controllers.pagos_controller import (
    historial_pagos_paginado_controller,
    MigracionPagosAdelantadosPendienteError,
    obtener_opciones_adelanto_controller,
    obtener_opciones_vencidas_controller,
    registrar_pago_adelantado_controller,
    registrar_pago_controller,
    historial_pagos_controller,
    anular_pago_controller
)

router = APIRouter(tags=["Pagos"], dependencies=[Depends(get_current_active_admin)])


# 💰 Registrar pago
@router.post("/pagos")
def registrar_pago(pago: PagoCreate):
    try:
        pago_id = registrar_pago_controller(pago)
    except MigracionPagosAdelantadosPendienteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "mensaje": "Pago registrado correctamente",
        "pago_id": pago_id
    }


@router.get("/pagos/vencidos/opciones/{estudiante_id}")
def opciones_pago_vencido(estudiante_id: int):
    try:
        return obtener_opciones_vencidas_controller(estudiante_id)
    except MigracionPagosAdelantadosPendienteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/pagos/adelanto/opciones/{estudiante_id}")
def opciones_pago_adelantado(estudiante_id: int):
    try:
        return obtener_opciones_adelanto_controller(estudiante_id)
    except MigracionPagosAdelantadosPendienteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/pagos/adelanto")
def registrar_pago_adelantado(pago: PagoAdelantadoCreate):
    try:
        return registrar_pago_adelantado_controller(pago)
    except MigracionPagosAdelantadosPendienteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# 📄 Ver historial
@router.get("/pagos/{estudiante_id}")
def historial_pagos(
    estudiante_id: int,
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if limit is not None:
        return historial_pagos_paginado_controller(estudiante_id, limit=limit, offset=offset)
    return historial_pagos_controller(estudiante_id)


@router.post("/pagos/{pago_id}/anular")
def anular_pago(
    pago_id: int,
    data: PagoAnular,
    current_user: dict = Depends(get_current_active_admin),
):
    try:
        return anular_pago_controller(pago_id, data.motivo, current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
