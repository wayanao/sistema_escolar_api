from typing import Annotated, List, Literal, Optional
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, conint, confloat, model_validator

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
    listar_valores_personalizados_estudiante,
    upsert_valor_personalizado_estudiante,
    eliminar_valor_personalizado_estudiante,
    MigracionPendienteError,
    ConfiguracionTipoPagoInvalidaError,
    CursoDeOtroAnioError,
    TipoPagoDuplicadoError,
    TipoPagoInfraestructuraError,
)

router = APIRouter(tags=["Tipos Pagos"], dependencies=[Depends(get_current_active_admin)])

_ERROR_INTERNO_TIPOS_PAGO = "Error interno al procesar la operación de tipos de pago"


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
    mes_final: conint(ge=1, le=12) = 12
    frecuencia_meses: Optional[conint(ge=1, le=12)] = None
    generacion_automatica: Optional[bool] = None
    activo: Optional[bool] = None

    @model_validator(mode="after")
    def validar_rango_meses(self):
        if (
            self.tipo_cobro == "mensual"
            and self.mes_inicial is not None
            and self.mes_final < self.mes_inicial
        ):
            raise ValueError("El mes final no puede ser anterior al mes inicial.")
        return self


class CursoAsignacionItem(BaseModel):
    curso_id: int
    valor: confloat(ge=0) = 0
    activo: bool = True


class CursoAsignacionPayload(BaseModel):
    cursos: List[CursoAsignacionItem] = Field(default_factory=list)


class ValorPersonalizadoEstudiante(BaseModel):
    valor: confloat(ge=0)
    motivo: Optional[str] = None
    activo: bool = True


# -----------------------------------------------------------------------------
# CRUD básico (sin cambios)
# -----------------------------------------------------------------------------
@router.post('/tipos-pagos')
def create_tipo_pago(tipo: TipoPago):
    try:
        res = crear_tipo_pago(tipo.nombre, tipo.valor)
    except TipoPagoDuplicadoError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TipoPagoInfraestructuraError:
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_TIPOS_PAGO)

    if not res:
        raise HTTPException(status_code=400, detail='No se pudo crear el tipo de pago')
    return res


@router.get('/tipos-pagos')
def get_tipos_pagos(anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None):
    """Sin `anio_lectivo_id`, los conceptos del año activo."""
    try:
        return listar_tipos_pagos(anio_lectivo_id=anio_lectivo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put('/tipos-pagos/{id}')
def update_tipo_pago(id: int, tipo: TipoPago):
    try:
        res = actualizar_tipo_pago(id, tipo.nombre, tipo.valor)
    except TipoPagoDuplicadoError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TipoPagoInfraestructuraError:
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_TIPOS_PAGO)

    if not res:
        raise HTTPException(status_code=400, detail='Error al actualizar')
    return {"message": "Actualizado correctamente"}


@router.delete('/tipos-pagos/{id}')
def delete_tipo_pago(id: int):
    res = eliminar_tipo_pago(id)
    raise HTTPException(status_code=405, detail=res["error"])


# -----------------------------------------------------------------------------
# Configuración avanzada
# -----------------------------------------------------------------------------
@router.get('/tipos-pagos/detallado')
def get_tipos_pagos_detallado(anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None):
    """Tipos de pago de un año con configuración financiera y cursos.

    Sin `anio_lectivo_id`, los del año activo.
    """
    try:
        return listar_tipos_pagos_detallado(anio_lectivo_id=anio_lectivo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
    except ConfiguracionTipoPagoInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TipoPagoInfraestructuraError:
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_TIPOS_PAGO)

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
    try:
        res = upsert_cursos_asignados(id, [c.model_dump() for c in payload.cursos])
    except CursoDeOtroAnioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TipoPagoInfraestructuraError:
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_TIPOS_PAGO)

    if res is None:
        raise HTTPException(status_code=400, detail='No se pudo asignar cursos')
    return {"message": "Cursos asignados", "cursos": res}


@router.delete('/tipos-pagos/{id}/cursos/{curso_id}')
def delete_curso_asignado(id: int, curso_id: int):
    try:
        res = eliminar_curso_asignado(id, curso_id)
    except TipoPagoInfraestructuraError:
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_TIPOS_PAGO)

    if not res:
        raise HTTPException(status_code=404, detail='Asignación no encontrada')
    return {"message": "Curso desasignado"}


# -----------------------------------------------------------------------------
# Valores personalizados por estudiante
# -----------------------------------------------------------------------------
@router.get('/estudiantes/{estudiante_id}/valores-pago-personalizados')
def get_valores_personalizados_estudiante(estudiante_id: int):
    try:
        return listar_valores_personalizados_estudiante(estudiante_id)
    except MigracionPendienteError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put('/estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}')
def put_valor_personalizado_estudiante(
    estudiante_id: int,
    tipo_pago_id: int,
    payload: ValorPersonalizadoEstudiante,
):
    try:
        res = upsert_valor_personalizado_estudiante(
            estudiante_id,
            tipo_pago_id,
            payload.valor,
            motivo=payload.motivo,
            activo=payload.activo,
        )
    except MigracionPendienteError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TipoPagoInfraestructuraError:
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_TIPOS_PAGO)

    if res is None:
        raise HTTPException(status_code=400, detail='No se pudo guardar el valor personalizado')
    return {"message": "Valor personalizado guardado", "valores": res}


@router.delete('/estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}')
def delete_valor_personalizado_estudiante(estudiante_id: int, tipo_pago_id: int):
    try:
        res = eliminar_valor_personalizado_estudiante(estudiante_id, tipo_pago_id)
    except MigracionPendienteError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TipoPagoInfraestructuraError:
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_TIPOS_PAGO)

    if not res:
        raise HTTPException(status_code=404, detail='Valor personalizado no encontrado')
    return {"message": "Valor personalizado eliminado"}
