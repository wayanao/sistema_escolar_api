from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Annotated, Optional
from datetime import date
from app.controllers.prestamo_controller import obtener_prestamos, crear_prestamo, eliminar_prestamo, actualizar_estado_prestamo
from app.dependencies import get_current_active_admin

router = APIRouter(prefix="/api/prestamos", tags=["Prestamos"])

class PrestamoCreate(BaseModel):
    profesor_id: int
    monto: float
    fecha: Optional[date] = None
    estado: Optional[str] = "Pendiente"
    notas: Optional[str] = ""

class EstadoUpdate(BaseModel):
    estado: str

@router.get("/")
def get_prestamos(
    profesor_id: Annotated[Optional[int], Query()] = None,
    current_admin: dict = Depends(get_current_active_admin),
):
    return obtener_prestamos(profesor_id=profesor_id)

@router.post("/")
def add_prestamo(prestamo: PrestamoCreate, current_admin: dict = Depends(get_current_active_admin)):
    try:
        return crear_prestamo(prestamo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.put("/{prestamo_id}/estado")
def update_estado(prestamo_id: int, estado: EstadoUpdate, current_admin: dict = Depends(get_current_active_admin)):
    try:
        return actualizar_estado_prestamo(prestamo_id, estado.estado)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.delete("/{prestamo_id}")
def delete_prestamo(prestamo_id: int, current_admin: dict = Depends(get_current_active_admin)):
    resultado = eliminar_prestamo(prestamo_id)
    raise HTTPException(status_code=405, detail=resultado["error"])
