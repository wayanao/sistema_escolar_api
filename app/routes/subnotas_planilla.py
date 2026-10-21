"""Subnotas de la planilla. Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`.

Cuatro rutas: crear una subnota, renombrarla, borrarla y guardar las
calificaciones de un estudiante en un tipo de nota. La lectura va en la
planilla de siempre, con `GET /planilla-excel/...?con_subnotas=true`.

Van en un router propio, y no en `planilla.py`, para que las tres rutas viejas
de la planilla sigan exactamente como estaban.

Esta capa **no tiene reglas**: recibe, llama al controlador y traduce sus
errores a codigos HTTP. El permiso de la asignacion, el año lectivo y que el
estudiante sea del curso los comprueba el controlador, con la conexion que ya
abrio. `str(exc)` es seguro aqui: los errores propios llevan mensajes
constantes escritos a mano, nunca texto de PostgreSQL.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.subnotas_planilla_controller import (
    CalificacionInvalidaError,
    ErrorDeSubnotas,
    LimiteDeSubnotasError,
    SubnotaDuplicadaError,
    SubnotaNoEncontradaError,
    SubnotasAjenasError,
    TipoNoEncontradoError,
    TipoSinSubnotasError,
    crear_subnota_controller,
    eliminar_subnota_controller,
    guardar_calificaciones_controller,
    renombrar_subnota_controller,
)
from app.dependencies import get_current_user
from app.schemas.subnotas_planilla import (
    CalificacionesCreate,
    SubnotaCreate,
    SubnotaRename,
)


router = APIRouter(
    prefix="/planilla/subnotas",
    tags=["Planilla"],
    dependencies=[Depends(get_current_user)],
)

_CODIGOS = {
    TipoNoEncontradoError: status.HTTP_404_NOT_FOUND,
    SubnotaNoEncontradaError: status.HTTP_404_NOT_FOUND,
    SubnotaDuplicadaError: status.HTTP_409_CONFLICT,
    TipoSinSubnotasError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    LimiteDeSubnotasError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    SubnotasAjenasError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    CalificacionInvalidaError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _responder(controlador, *args, **kwargs):
    try:
        return controlador(*args, **kwargs)
    except ErrorDeSubnotas as exc:
        raise HTTPException(status_code=_CODIGOS[type(exc)], detail=str(exc)) from exc


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_subnota(datos: SubnotaCreate, current_user: dict = Depends(get_current_user)):
    """Crea la subnota para todo el curso. Devuelve su id y su nombre recortado."""
    return _responder(crear_subnota_controller, datos, usuario=current_user)


@router.post("/valores")
def guardar_calificaciones(
    datos: CalificacionesCreate, current_user: dict = Depends(get_current_user)
):
    """Guarda las subnotas de un estudiante y devuelve su celda recalculada."""
    return _responder(guardar_calificaciones_controller, datos, usuario=current_user)


@router.put("/{subnota_id}")
def renombrar_subnota(
    subnota_id: int, datos: SubnotaRename, current_user: dict = Depends(get_current_user)
):
    return _responder(renombrar_subnota_controller, subnota_id, datos, usuario=current_user)


@router.delete("/{subnota_id}")
def eliminar_subnota(
    subnota_id: int, asignacion_id: int, current_user: dict = Depends(get_current_user)
):
    """Borra la subnota y devuelve las celdas que cambiaron."""
    return _responder(
        eliminar_subnota_controller, subnota_id, asignacion_id, usuario=current_user
    )
