from typing import List, Literal, Optional
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, conint, confloat

from app.dependencies import get_current_active_admin, HTTPException
from app.controllers.tipos_pagos_controller import (
    crear_tipo_pago,
    listar_tipos_pagos,
    actualizar_tipo_pago,
    eliminar_tipo_pago,
    obtener_tipo_pago,
    listar_tipos_pagos_detallado,
    actualizar_configuracion_tipo_pago,
    listar_cursos_asignados,
    upsert_cursos_asignados,
    eliminar_curso_asignado,
    MigracionPendienteError,
    TipoPagoDuplicadoError,
)

router = APIRouter(tags=["Tipos Pagos"], dependencies=[Depends(get_current_active_admin)])


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class TipoPago(BaseModel):
    nombre: str
    valor: float = 0.0


TipoCobro = Literal["unico", "mensual", "anual", "opcional"]
MoraTipo = Literal["porcentaje", "fijo"]


class ConfiguracionTipoPago(BaseModel):
    descripcion: Optional[str] = None
    tipo_cobro: Optional[TipoCobro] = None
    fecha_limite: Optional[date] = None
    dia_limite_mes: Optional[conint(ge=1, le=31)] = None
    dias_gracia: Optional[conint(ge=0, le=365)] = None
    mora_tipo: Optional[MoraTipo] = None
    mora_valor: Optional[confloat(ge=0)] = None
    mes_inicial: Optional[conint(ge=1, le=12)] = None
    frecuencia_meses: Optional[conint(ge=1, le=12)] = None
    generacion_automatica: Optional[bool] = None
    activo: Optional[bool] = None


class CursoAsignacionItem(BaseModel):
    curso_id: int
    valor: confloat(ge=0) = 0
    activo: bool = True


class CursoAsignacionPayload(BaseModel):
    cursos: List[CursoAsignacionItem] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# CRUD básico (sin cambios)
# -----------------------------------------------------------------------------
@router.post('/tipos-pagos')
def create_tipo_pago(tipo: TipoPago):
    try:
        res = crear_tipo_pago(tipo.nombre, tipo.valor)
    except TipoPagoDuplicadoError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not res:
        raise HTTPException(status_code=400, detail='No se pudo crear el tipo de pago')
    return res


@router.get('/tipos-pagos')
def get_tipos_pagos():
    return listar_tipos_pagos()


@router.put('/tipos-pagos/{id}')
def update_tipo_pago(id: int, tipo: TipoPago):
    try:
        res = actualizar_tipo_pago(id, tipo.nombre, tipo.valor)
    except TipoPagoDuplicadoError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not res:
        raise HTTPException(status_code=400, detail='Error al actualizar')
    return {"message": "Actualizado correctamente"}


@router.delete('/tipos-pagos/{id}')
def delete_tipo_pago(id: int):
    res = eliminar_tipo_pago(id)
    if not res:
        raise HTTPException(status_code=400, detail='Error al eliminar')
    return {"message": "Eliminado correctamente"}


# -----------------------------------------------------------------------------
# Configuración avanzada
# -----------------------------------------------------------------------------
@router.get('/tipos-pagos/detallado')
def get_tipos_pagos_detallado():
    """Lista todos los tipos de pago con configuración financiera y cursos."""
    return listar_tipos_pagos_detallado()


@router.get('/tipos-pagos/{id}/detalle')
def get_tipo_pago_detalle(id: int):
    tipo = obtener_tipo_pago(id)
    if not tipo:
        raise HTTPException(status_code=404, detail='Tipo de pago no encontrado')
    tipo["cursos"] = listar_cursos_asignados(id)
    return tipo


@router.put('/tipos-pagos/{id}/configuracion')
def update_configuracion_tipo_pago(id: int, config: ConfiguracionTipoPago):
    payload = config.model_dump(exclude_unset=True)
    if "fecha_limite" in payload and payload["fecha_limite"] is not None:
        payload["fecha_limite"] = payload["fecha_limite"].isoformat()

    try:
        res = actualizar_configuracion_tipo_pago(id, payload)
    except MigracionPendienteError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not res:
        raise HTTPException(status_code=400, detail='No se pudo actualizar la configuración')
    return {"message": "Configuración actualizada", "tipo_pago": obtener_tipo_pago(id)}


# -----------------------------------------------------------------------------
# Asignación a cursos
# -----------------------------------------------------------------------------
@router.get('/tipos-pagos/{id}/cursos')
def get_cursos_asignados(id: int):
    return listar_cursos_asignados(id)


@router.put('/tipos-pagos/{id}/cursos')
def put_cursos_asignados(id: int, payload: CursoAsignacionPayload):
    res = upsert_cursos_asignados(id, [c.model_dump() for c in payload.cursos])
    if res is None:
        raise HTTPException(status_code=400, detail='No se pudo asignar cursos')
    return {"message": "Cursos asignados", "cursos": res}


@router.delete('/tipos-pagos/{id}/cursos/{curso_id}')
def delete_curso_asignado(id: int, curso_id: int):
    res = eliminar_curso_asignado(id, curso_id)
    if not res:
        raise HTTPException(status_code=404, detail='Asignación no encontrada')
    return {"message": "Curso desasignado"}
