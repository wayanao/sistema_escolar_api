"""Porcentajes por tipo de nota. Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`.

Una ruta: guardar, cambiar o quitar el porcentaje de un tipo de nota. La
lectura va en la planilla de siempre, con
`GET /planilla-excel/...?con_porcentajes=true`.

Va en un router propio, como las subnotas, para que las rutas viejas de la
planilla sigan exactamente como estaban. Esta capa **no tiene reglas**:
recibe, llama al controlador y traduce sus errores a codigos HTTP. `str(exc)`
es seguro aqui: los errores propios llevan mensajes constantes escritos a
mano, nunca texto de PostgreSQL.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.porcentajes_planilla_controller import (
    ErrorDePorcentajes,
    PorcentajeInvalidoError,
    SumaExcedidaError,
    TipoNoEncontradoError,
    TipoSinPorcentajeError,
    guardar_porcentaje_controller,
)
from app.dependencies import get_current_user
from app.schemas.porcentajes_planilla import PorcentajeTipoUpdate


router = APIRouter(
    prefix="/planilla/tipos",
    tags=["Planilla"],
    dependencies=[Depends(get_current_user)],
)

_CODIGOS = {
    TipoNoEncontradoError: status.HTTP_404_NOT_FOUND,
    TipoSinPorcentajeError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    PorcentajeInvalidoError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    SumaExcedidaError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


@router.put("/porcentaje")
def guardar_porcentaje(
    datos: PorcentajeTipoUpdate, current_user: dict = Depends(get_current_user)
):
    """Guarda el porcentaje de un tipo (o lo quita con `null`) y devuelve la
    suma de la clase y si los porcentajes quedaron activos."""
    try:
        return guardar_porcentaje_controller(datos, usuario=current_user)
    except ErrorDePorcentajes as exc:
        raise HTTPException(status_code=_CODIGOS[type(exc)], detail=str(exc)) from exc
