"""Admisiones (entrevista de admisión), paso E2.

Ver `docs/funcionalidades/ENTREVISTA_ADMISION.md`, sección "Rutas".

**Solo admin, a nivel de router**, como `listas_seguimiento.py`: así una ruta
nueva nace protegida. Son datos personales de menores (Ley 1581 de 2012).

Esta capa no tiene reglas de negocio: recibe, llama al controlador y traduce
sus errores a códigos HTTP. `str(exc)` es seguro: los mensajes son constantes
del controlador o de `app/services/anio_lectivo.py`, no texto de PostgreSQL.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.controllers.admisiones_controller import (
    AdmisionMatriculadaError,
    AdmisionNoEncontradaError,
    AnioNoEnPreparacionError,
    CursoAdmisionInvalidoError,
    DocumentoAdmisionRepetidoError,
    actualizar_admision_controller,
    borrar_admision_controller,
    listar_admisiones_controller,
    obtener_admision_controller,
    registrar_admision_controller,
)
from app.dependencies import get_current_active_admin
from app.schemas.admision import AdmisionCreate, AdmisionUpdate, ResultadoAdmision
from app.services.anio_lectivo import AnioLectivoInexistenteError


router = APIRouter(
    tags=["Admisiones"],
    dependencies=[Depends(get_current_active_admin)],
)

_NO_EXISTE = (AnioLectivoInexistenteError, AdmisionNoEncontradaError)
_ERRORES = _NO_EXISTE + (
    AnioNoEnPreparacionError,
    AdmisionMatriculadaError,
    CursoAdmisionInvalidoError,
    DocumentoAdmisionRepetidoError,
)


def _traducir_error(exc):
    if isinstance(exc, _NO_EXISTE):
        codigo = status.HTTP_404_NOT_FOUND
    else:
        codigo = status.HTTP_409_CONFLICT
    raise HTTPException(status_code=codigo, detail=str(exc)) from exc


@router.get("/anios-lectivos/{anio_lectivo_id}/admisiones")
def listar_admisiones(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    resultado: Annotated[Optional[ResultadoAdmision], Query()] = None,
):
    """Las admisiones del año (opcional, de un resultado), con conteos."""
    try:
        return listar_admisiones_controller(anio_lectivo_id, resultado)
    except _ERRORES as exc:
        _traducir_error(exc)


@router.post(
    "/anios-lectivos/{anio_lectivo_id}/admisiones",
    status_code=status.HTTP_201_CREATED,
)
def registrar_admision(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    datos: AdmisionCreate,
):
    """Registra un aspirante en el año en preparación. Queda pendiente."""
    try:
        return registrar_admision_controller(anio_lectivo_id, datos)
    except _ERRORES as exc:
        _traducir_error(exc)


@router.get("/admisiones/{admision_id}")
def obtener_admision(admision_id: Annotated[int, Path(gt=0)]):
    """Una admisión completa."""
    try:
        return obtener_admision_controller(admision_id)
    except _ERRORES as exc:
        _traducir_error(exc)


@router.put("/admisiones/{admision_id}")
def actualizar_admision(
    admision_id: Annotated[int, Path(gt=0)],
    datos: AdmisionUpdate,
):
    """Edita aspirante y entrevista. No cambia el resultado."""
    try:
        return actualizar_admision_controller(admision_id, datos)
    except _ERRORES as exc:
        _traducir_error(exc)


@router.delete("/admisiones/{admision_id}")
def borrar_admision(admision_id: Annotated[int, Path(gt=0)]):
    """Borra una admisión que todavía no se matriculó (decisión 9)."""
    try:
        return borrar_admision_controller(admision_id)
    except _ERRORES as exc:
        _traducir_error(exc)
