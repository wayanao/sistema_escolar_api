"""Años lectivos: listado y creación del siguiente año en preparación.

Ver docs/funcionalidades/ANIO_LECTIVO.md (fase 3, paso 3.1, y fase 5, paso
5.3). Qué años ve cada usuario lo decide `app/services/anio_lectivo.py`.
"""
from app.database import get_cursor
from app.repositories import anios_lectivos_repository
from app.services.anio_lectivo import listar_anios_visibles


class AnioLectivoEnPreparacionError(Exception):
    """Ya existe el único año que se puede preparar a la vez."""


class AnioLectivoActivoInexistenteError(Exception):
    """No hay año activo desde el cual calcular exactamente N+1."""


class AnioLectivoSiguienteExistenteError(Exception):
    """El N+1 calculado ya existe y no se puede duplicar."""


def _formatear_anio(row):
    return {
        "id": row[0],
        "anio": row[1],
        "estado": row[2],
    }


def listar_anios_lectivos_controller(usuario):
    with get_cursor() as cursor:
        filas = listar_anios_visibles(cursor, usuario)
    return [_formatear_anio(row) for row in filas]


def crear_anio_lectivo_controller():
    """Crea exactamente el año posterior al activo, en preparación."""
    with get_cursor(commit=True) as cursor:
        activo = anios_lectivos_repository.leer_anio_activo_para_actualizar(cursor)
        if activo is None:
            raise AnioLectivoActivoInexistenteError(
                "No hay un año lectivo activo para calcular el siguiente."
            )

        if anios_lectivos_repository.leer_anio_en_preparacion(cursor) is not None:
            raise AnioLectivoEnPreparacionError(
                "Ya hay un año lectivo en preparación."
            )

        siguiente = activo[1] + 1
        creado = anios_lectivos_repository.crear_anio_en_preparacion(
            cursor, siguiente
        )
        if creado is None:
            raise AnioLectivoSiguienteExistenteError(
                f"El año lectivo {siguiente} ya existe o está en preparación."
            )

    return _formatear_anio(creado)
