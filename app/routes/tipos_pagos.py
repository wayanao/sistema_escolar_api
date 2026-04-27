from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, HTTPException
from pydantic import BaseModel
from app.controllers.tipos_pagos_controller import crear_tipo_pago, listar_tipos_pagos, actualizar_tipo_pago, eliminar_tipo_pago

router = APIRouter(tags=["Tipos Pagos"], dependencies=[Depends(get_current_user)])

class TipoPago(BaseModel):
    nombre: str
    valor: float = 0.0

@router.post('/tipos-pagos')
def create_tipo_pago(tipo: TipoPago):
    res = crear_tipo_pago(tipo.nombre, tipo.valor)
    if not res:
        raise HTTPException(status_code=400, detail='Error o tipo de pago ya existe')
    return res

@router.get('/tipos-pagos')
def get_tipos_pagos():
    return listar_tipos_pagos()

@router.put('/tipos-pagos/{id}')
def update_tipo_pago(id: int, tipo: TipoPago):
    res = actualizar_tipo_pago(id, tipo.nombre, tipo.valor)
    if not res:
        raise HTTPException(status_code=400, detail='Error al actualizar')
    return {"message": "Actualizado correctamente"}

@router.delete('/tipos-pagos/{id}')
def delete_tipo_pago(id: int):
    res = eliminar_tipo_pago(id)
    if not res:
        raise HTTPException(status_code=400, detail='Error al eliminar')
    return {"message": "Eliminado correctamente"}