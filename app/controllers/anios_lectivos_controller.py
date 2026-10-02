"""Años lectivos: la lista que alimenta el selector de año del frontend.

Ver docs/funcionalidades/ANIO_LECTIVO.md (fase 3, paso 3.1). Que años ve cada
usuario lo decide `app/services/anio_lectivo.py`, no este archivo.
"""
from app.database import get_cursor
from app.services.anio_lectivo import listar_anios_visibles


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
