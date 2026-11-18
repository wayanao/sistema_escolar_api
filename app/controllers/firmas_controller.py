"""Firmas guardadas para el boletin. Ver docs/funcionalidades/FIRMAS_BOLETIN.md.

Quien puede llamar a cada funcion lo decide la ruta (`app/routes/firmas.py`):
la firma institucional, solo el admin; la de un profesor, solo ese profesor,
con el `id` de su sesion.
"""
from app.core.firmas import decodificar_firma, firma_para_responder
from app.database import get_cursor
from app.repositories import firmas_repository
from app.services.anio_lectivo import anio_distinto_del_activo


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


# --------------------------------------------------------------------------
# Firma del director de grupo, para el observador que imprime el admin
# --------------------------------------------------------------------------

def obtener_firma_director_grupo_controller(estudiante_id, anio_lectivo_id=None):
    """`{director_grupo, imagen, actualizado_en}` del curso del estudiante.

    `None` si el estudiante no existe (la ruta responde 404). Un año que no
    existe sube como `AnioLectivoInexistenteError`. Solo lee: no confirma.
    """
    with get_cursor() as cursor:
        anio = anio_distinto_del_activo(cursor, anio_lectivo_id)
        fila = firmas_repository.leer_firma_del_director_de_grupo(
            cursor, estudiante_id, anio
        )
    if fila is None:
        return None
    nombre, apellido, imagen_png, actualizado_en = fila
    director = " ".join(parte for parte in (nombre, apellido) if parte).strip()
    return {
        "director_grupo": director or None,
        **firma_para_responder(imagen_png, actualizado_en),
    }
