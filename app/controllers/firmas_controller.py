"""Firmas guardadas para el boletin. Ver docs/funcionalidades/FIRMAS_BOLETIN.md.

Quien puede llamar a cada funcion lo decide la ruta (`app/routes/firmas.py`):
la firma institucional, solo el admin; la de un profesor, solo ese profesor,
con el `id` de su sesion.
"""
from app.core.firmas import decodificar_firma, firma_para_responder
from app.database import get_cursor
from app.repositories import firmas_repository


def _respuesta(fila):
    if not fila:
        return firma_para_responder(None, None)
    return firma_para_responder(fila[0], fila[1])


# --------------------------------------------------------------------------
# Firma del rector(a)
# --------------------------------------------------------------------------

def obtener_firma_institucional_controller():
    with get_cursor() as cursor:
        fila = firmas_repository.leer_firma_institucional(cursor)
    return _respuesta(fila)


def guardar_firma_institucional_controller(imagen, usuario):
    """`imagen` ya paso por `FirmaIn`; se decodifica otra vez para tener los
    bytes. `usuario` es el admin de la sesion."""
    imagen_png = decodificar_firma(imagen)
    with get_cursor(commit=True) as cursor:
        fila = firmas_repository.guardar_firma_institucional(
            cursor, imagen_png, usuario["id"]
        )
    return firma_para_responder(imagen_png, fila[0] if fila else None)


def borrar_firma_institucional_controller():
    with get_cursor(commit=True) as cursor:
        firmas_repository.borrar_firma_institucional(cursor)
    return firma_para_responder(None, None)


# --------------------------------------------------------------------------
# Firma del profesor de la sesion
# --------------------------------------------------------------------------

def obtener_mi_firma_controller(profesor_id):
    with get_cursor() as cursor:
        fila = firmas_repository.leer_firma_de_profesor(cursor, profesor_id)
    return _respuesta(fila)


def guardar_mi_firma_controller(profesor_id, imagen):
    imagen_png = decodificar_firma(imagen)
    with get_cursor(commit=True) as cursor:
        fila = firmas_repository.guardar_firma_de_profesor(cursor, profesor_id, imagen_png)
    return firma_para_responder(imagen_png, fila[0] if fila else None)


def borrar_mi_firma_controller(profesor_id):
    with get_cursor(commit=True) as cursor:
        firmas_repository.borrar_firma_de_profesor(cursor, profesor_id)
    return firma_para_responder(None, None)
