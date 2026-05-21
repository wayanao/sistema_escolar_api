from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_active_admin
from app.schemas.inventario import InventarioCreate, InventarioUpdate
from app.controllers.inventario_controller import (
    obtener_inventario_paginado_controller,
    obtener_inventario_controller,
    crear_inventario_controller,
    actualizar_inventario_controller,
    eliminar_inventario_controller
)

router = APIRouter(tags=["Inventario"], dependencies=[Depends(get_current_active_admin)])

@router.get("/inventario")
def obtener_inventario(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
    solo_con_stock: bool = False,
):
    if limit is not None:
        return obtener_inventario_paginado_controller(
            limit=limit,
            offset=offset,
            busqueda=busqueda,
            solo_con_stock=solo_con_stock,
        )
    return obtener_inventario_controller()

@router.post("/inventario")
def crear_producto(producto: InventarioCreate):
    nuevo_id = crear_inventario_controller(producto)
    return {"mensaje": "Producto creado exitosamente", "id": nuevo_id}

@router.put("/inventario/{item_id}")
def actualizar_producto(item_id: int, producto: InventarioUpdate):
    actualizar_inventario_controller(item_id, producto)
    return {"mensaje": "Producto actualizado exitosamente"}

@router.delete("/inventario/{item_id}")
def eliminar_producto(item_id: int):
    eliminar_inventario_controller(item_id)
    return {"mensaje": "Producto eliminado exitosamente"}
