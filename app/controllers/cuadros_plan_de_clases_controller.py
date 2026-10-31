"""Leer y guardar los nombres de los cuadros del plan de clase.

Ver `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`. Lo que es valido lo decide
`app/core/cuadros_plan_de_clases.py`; este modulo lee, llama y escribe. Su
error propio lleva un mensaje **constante** y la ruta lo traduce a 422.

Consultas, sin contar la sesion: leer, 1. Guardar, 3 (bloquear, borrar e
insertar) en una sola transaccion, o 2 al volver a los originales. Una lista
invalida se rechaza antes de abrir la base.
"""
from app.core.cuadros_plan_de_clases import en_orden_del_formulario, motivo_para_rechazar
from app.database import get_cursor
from app.repositories import cuadros_plan_de_clases_repository as repositorio


class CuadrosInvalidosError(Exception):
    """La lista no se puede guardar. La ruta lo traduce a 422."""


def leer_cuadros_controller():
    """Los cuadros renombrados del colegio, en el orden del formulario."""
    with get_cursor() as cursor:
        filas = repositorio.leer_cuadros(cursor)
    return {"cuadros": en_orden_del_formulario(filas)}


def guardar_cuadros_controller(datos, *, usuario):
    """Reemplaza todos los nombres del colegio por los de `datos`.

    Todo o nada: se borra e inserta en la misma transaccion. Una lista vacia
    deja todos los cuadros con su nombre original. Devuelve lo guardado, igual
    que la lectura.
    """
    cuadros = [(cuadro.clave, cuadro.nombre, cuadro.ayuda) for cuadro in datos.cuadros]
    motivo = motivo_para_rechazar(cuadros)
    if motivo:
        raise CuadrosInvalidosError(motivo)

    with get_cursor(commit=True) as cursor:
        repositorio.bloquear_cuadros(cursor)
        repositorio.borrar_cuadros(cursor)
        if cuadros:
            repositorio.insertar_cuadros(cursor, cuadros, usuario["id"])
    return {"cuadros": en_orden_del_formulario(cuadros)}
