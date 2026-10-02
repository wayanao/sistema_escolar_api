"""Reglas del año lectivo que comparten varios modulos.

Ver docs/funcionalidades/ANIO_LECTIVO.md. Es el servicio que el documento
preve para el año lectivo; por ahora solo valida el año que se pide.
"""
from app.repositories.anios_lectivos_repository import leer_anio_lectivo


def exigir_anio_lectivo(cursor, anio_lectivo_id):
    """Devuelve el año pedido como `(id, anio, estado)`.

    Lanza `ValueError`, con un mensaje listo para mostrar, si no existe.
    Cualquier estado vale: un pago se registra en el año de la deuda que
    salda, aunque ese año este cerrado (decision 6).
    """
    anio = leer_anio_lectivo(cursor, anio_lectivo_id)
    if anio is None:
        raise ValueError("El año lectivo seleccionado no existe.")
    return anio
