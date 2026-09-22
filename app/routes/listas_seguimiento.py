"""Listas de Seguimiento por Curso.

Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`. Cuatro endpoints: leer la
lista completa de un curso, crear una columna, borrarla, y guardar un lote de
marcas.

**Solo admin, a nivel de router.** Es el mismo `Depends` que llevan
`tipos_pagos.py` y `cursos.py`, y se pone en el `APIRouter` y no en cada
funcion: asi un endpoint nuevo nace protegido en vez de nacer abierto y
depender de que alguien se acuerde. Los helpers de `app/core/permissions.py`
no se usan aqui porque acotan a un profesor a sus propias asignaciones, y esta
pantalla no la ve ningun profesor.

Esta capa **no tiene reglas de negocio**: recibe, llama al controlador y
traduce sus errores a codigos HTTP. Todo lo que decide vive en
`listas_seguimiento_controller`.

`str(exc)` si es seguro en este modulo, al contrario de lo que avisa
`observador.py`: los cuatro errores que se atrapan aqui llevan mensajes que
son constantes escritas a mano en el controlador, no texto de PostgreSQL. El
controlador se encarga de que nunca lo sean, y tiene prueba que lo verifica.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.listas_seguimiento_controller import (
    ColumnaDuplicadaError,
    ColumnaNoEncontradaError,
    CursoNoEncontradoError,
    MarcasFueraDelCursoError,
    crear_columna_controller,
    eliminar_columna_controller,
    guardar_marcas_controller,
    obtener_lista_seguimiento_controller,
)
from app.dependencies import get_current_active_admin
from app.schemas.listas_seguimiento import ColumnaSeguimientoCreate, LoteDeMarcas


router = APIRouter(
    prefix="/listas-seguimiento",
    tags=["Listas Seguimiento"],
    dependencies=[Depends(get_current_active_admin)],
)


@router.get("/{curso_id}")
def obtener_lista_seguimiento(curso_id: int):
    """Columnas, alumnos y marcas del curso, en una sola respuesta.

    Una sola peticion para pintar la pantalla entera. Pedir las marcas aparte,
    o una peticion por alumno, es justo lo que la pantalla vieja del
    observador hacia y lo que costo 16-20 s.
    """
    try:
        return obtener_lista_seguimiento_controller(curso_id)
    except CursoNoEncontradoError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post("/{curso_id}/columnas", status_code=status.HTTP_201_CREATED)
def crear_columna(curso_id: int, columna: ColumnaSeguimientoCreate):
    """Crea una columna en el curso.

    Devuelve el id y el nombre ya recortado, para que la pantalla la pueda
    anadir a la grilla sin volver a pedir la lista completa.
    """
    try:
        columna_id = crear_columna_controller(curso_id, columna.nombre)
    except CursoNoEncontradoError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ColumnaDuplicadaError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return {"id": columna_id, "nombre": columna.nombre}


@router.delete("/{curso_id}/columnas/{columna_id}")
def eliminar_columna(curso_id: int, columna_id: int):
    """Borra la columna y, en cascada, todas sus marcas.

    Una columna de otro curso da el mismo 404 que una que no existe: el
    borrado se acota por curso dentro del propio DELETE.
    """
    try:
        eliminar_columna_controller(curso_id, columna_id)
    except ColumnaNoEncontradaError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return {"mensaje": "Columna eliminada"}


@router.post("/{curso_id}/marcas")
def guardar_marcas(curso_id: int, marcas: LoteDeMarcas):
    """Guarda el lote entero de celdas.

    El cuerpo es una lista pelada, el mismo formato que `POST /asistencia`.

    **El tipo tiene que ser `LoteDeMarcas` y no `list[MarcaSeguimientoItem]`.**
    Parecen lo mismo y no lo son: el primero lleva encima las dos reglas del
    lote -no vacio y sin celdas repetidas-, y sin ellas un lote con la misma
    celda repetida llegaria hasta PostgreSQL, que aborta la sentencia entera y
    devolveria un 500 en vez del 422 que promete el documento. Hay prueba que
    lo fija.
    """
    try:
        guardadas = guardar_marcas_controller(curso_id, marcas)
    except MarcasFueraDelCursoError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return {"mensaje": "Cambios guardados", "guardadas": guardadas}
