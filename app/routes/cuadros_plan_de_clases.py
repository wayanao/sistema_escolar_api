"""Nombres de los cuadros del plan de clase. Ver `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`.

Leer es para cualquier usuario del colegio (profesor o admin); guardar, solo
para el admin. No hay guardia de año lectivo: los nombres son del colegio, no
de un año.

Va en un router propio para que las rutas del plan de clases sigan
exactamente como estaban. **`app/main.py` lo incluye antes que
`plan_de_clases.router`**: si no, `GET /plan-de-clases/{asignacion_id}` atrapa
`/plan-de-clases/cuadros` y responde 422 al no poder leer "cuadros" como
numero.

Esta capa **no tiene reglas**: recibe, llama al controlador y traduce su error
a 422. `str(exc)` es seguro aqui: el mensaje es constante, escrito a mano.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.cuadros_plan_de_clases_controller import (
    CuadrosInvalidosError,
    guardar_cuadros_controller,
    leer_cuadros_controller,
)
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas.cuadros_plan_de_clases import CuadrosPlanUpdate


router = APIRouter(tags=["Plan De Clases"])


@router.get("/plan-de-clases/cuadros", dependencies=[Depends(get_current_user)])
def leer_cuadros():
    """Los cuadros que el colegio renombro. Lista vacia: todos con su nombre original."""
    return leer_cuadros_controller()


@router.put("/admin/plan-de-clases/cuadros")
def guardar_cuadros(
    datos: CuadrosPlanUpdate, current_user: dict = Depends(get_current_active_admin)
):
    """Reemplaza la lista completa de cuadros renombrados."""
    try:
        return guardar_cuadros_controller(datos, usuario=current_user)
    except CuadrosInvalidosError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
