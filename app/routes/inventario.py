from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies import get_current_active_admin
from app.schemas.inventario import InventarioCreate, InventarioEstadoUpdate, InventarioUpdate
from app.controllers.inventario_controller import (
    actualizar_estado_inventario_controller,
    obtener_inventario_paginado_controller,
    obtener_inventario_controller,
    crear_inventario_controller,
    actualizar_inventario_controller,
    eliminar_inventario_controller
)

router = APIRouter(tags=["Inventario"], dependencies=[Depends(get_current_active_admin)])

ESTADOS_INVENTARIO_FILTRO = {"activo", "inactivo", "todos"}


def validar_estado_filtro(estado: str) -> str:
    estado_normalizado = str(estado or "activo").strip().lower()
    if estado_normalizado not in ESTADOS_INVENTARIO_FILTRO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Estado de producto inválido.",
        )
    return estado_normalizado


@router.get("/inventario")
def obtener_inventario(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
    solo_con_stock: bool = False,
    estado: str = "activo",
):
    estado = validar_estado_filtro(estado)
    if limit is not None:
        return obtener_inventario_paginado_controller(
            limit=limit,
            offset=offset,
            busqueda=busqueda,
            solo_con_stock=solo_con_stock,
            estado=estado,
        )
    return obtener_inventario_controller(estado=estado)

@router.post("/inventario")
def crear_producto(producto: InventarioCreate):
    nuevo_id = crear_inventario_controller(producto)
    return {"mensaje": "Producto creado exitosamente", "id": nuevo_id}

@router.put("/inventario/{item_id}")
def actualizar_producto(item_id: int, producto: InventarioUpdate):
    actualizar_inventario_controller(item_id, producto)
    return {"mensaje": "Producto actualizado exitosamente"}

@router.patch("/inventario/{item_id}/estado")
def actualizar_estado_producto(item_id: int, payload: InventarioEstadoUpdate):
    resultado = actualizar_estado_inventario_controller(item_id, payload.estado)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado

@router.delete("/inventario/{item_id}")
def eliminar_producto(item_id: int):
    resultado = eliminar_inventario_controller(item_id)
    raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=resultado["error"])
