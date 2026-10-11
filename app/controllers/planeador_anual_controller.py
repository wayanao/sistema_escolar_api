from fastapi import HTTPException, status
from psycopg2 import IntegrityError, errorcodes

from app.core.permissions import require_asignacion_access
from app.database import get_connection, get_cursor
from app.repositories import planeador_anual_repository
from app.schemas.planeador_anual import PlaneadorAnualCreate, PlaneadorAnualUpdate
from app.services.anio_lectivo import (
    exigir_anio_editable,
    exigir_asignacion_editable,
    puede_guardar_en_anio,
)
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor
from typing import List

# Año lectivo, fase 7: traer el planeador del año pasado.
MENSAJE_PLANEADOR_TRAIDO = (
    "Se trajo el planeador del año pasado. Las fechas quedaron vacías: "
    "pon las de este año al guardar cada periodo."
)
MENSAJE_PLANEADOR_CON_CONTENIDO = (
    "Este planeador ya tiene contenido. No se trajo nada, para no "
    "reemplazar lo que ya está escrito."
)
MENSAJE_SIN_PLANEADOR_ANTERIOR = "No hay un planeador del año pasado para traer a esta clase."
MENSAJE_CLASE_INEXISTENTE = "La clase no existe."

def crear_planeador_anual_controller(planeador: PlaneadorAnualCreate):
    with get_cursor(commit=True) as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, planeador.asignacion_id)
        planeador_anual_repository.insertar_planeador_anual(
            cursor,
            asignacion_id,
            planeador.periodo,
            planeador.slot,
            planeador.unidad_tematica,
            planeador.estandar_competencia,
            planeador.contenido,
            planeador.actividades_recursos,
            planeador.fecha,
        )
        planeador_id = cursor.fetchone()[0]

    return planeador_id

def obtener_planeadores_anual_controller(asignacion_id: int, periodo: int) -> List[dict]:
    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        planeador_anual_repository.seleccionar_planeadores_anuales(
            cursor,
            asignacion_id,
            periodo,
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "asignacion_id": row[1],
            "periodo": row[2],
            "slot": row[3],
            "unidad_tematica": row[4],
            "estandar_competencia": row[5],
            "contenido": row[6],
            "actividades_recursos": row[7],
            "fecha": row[8]
        }
        for row in rows
    ]

def actualizar_planeador_anual_controller(planeador_id: int, planeador: PlaneadorAnualUpdate):
    with get_cursor(commit=True) as cursor:
        planeador_anual_repository.actualizar_planeador_anual(
            cursor,
            planeador_id,
            planeador.unidad_tematica,
            planeador.estandar_competencia,
            planeador.contenido,
            planeador.actividades_recursos,
            planeador.fecha,
        )

def bulk_actualizar_planeadores_controller(
    asignacion_id: int,
    periodo: int,
    planeadores: List[PlaneadorAnualUpdate],
    *,
    usuario,
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, asignacion_id, usuario)
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        for i, planeador in enumerate(planeadores):
            slot = i + 1
            tiene_contenido = any((
                planeador.unidad_tematica,
                planeador.estandar_competencia,
                planeador.contenido,
                planeador.actividades_recursos,
            ))

            if not tiene_contenido:
                planeador_anual_repository.eliminar_slot_planeador(
                    cursor,
                    asignacion_id,
                    periodo,
                    slot,
                )
                continue

            planeador_anual_repository.guardar_slot_planeador(
                cursor,
                asignacion_id,
                periodo,
                slot,
                planeador.unidad_tematica,
                planeador.estandar_competencia,
                planeador.contenido,
                planeador.actividades_recursos,
                planeador.fecha,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _contexto_planeador_anio_anterior(cursor, asignacion_id, usuario):
    """Permiso, clase académica y estado para traer el planeador del año pasado.

    En el cursor de quien llama: tres consultas para el profesor (su permiso,
    la clase académica y el estado) y dos para el admin. Devuelve
    `(destino_id, (anio, estado), tiene_filas, hay_origen)`.
    """
    require_asignacion_access(asignacion_id, usuario, cursor=cursor)
    destino_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
    fila = planeador_anual_repository.leer_planeador_anio_anterior(
        cursor, asignacion_id, destino_id
    )
    if fila is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_CLASE_INEXISTENTE)
    anio, estado, tiene_filas, hay_origen = fila
    return destino_id, (anio, estado), bool(tiene_filas), bool(hay_origen)


def consultar_planeador_anio_anterior_controller(asignacion_id: int, *, usuario) -> dict:
    """Si se ofrece el botón "Traer el planeador del año pasado" (decisión 14).

    `puede_traer` lo decide el backend: hay algo escrito que traer, el
    planeador de la clase está vacío y la guardia del año dejaría guardar a
    este usuario.
    """
    with get_cursor() as cursor:
        _, anio_y_estado, tiene_filas, hay_origen = _contexto_planeador_anio_anterior(
            cursor, asignacion_id, usuario
        )
    return {
        "hay_origen": hay_origen,
        "planeador_vacio": not tiene_filas,
        "puede_traer": (
            hay_origen and not tiene_filas and puede_guardar_en_anio(anio_y_estado, usuario)
        ),
    }


def traer_planeador_anio_anterior_controller(asignacion_id: int, *, usuario) -> dict:
    """Trae a la clase el planeador del año pasado, sin fechas.

    Nunca sobrescribe: si el planeador ya tiene alguna fila responde 409 y no
    copia nada. Sin nada que traer, 404. Todo en una transacción.
    """
    try:
        with get_cursor(commit=True) as cursor:
            destino_id, anio_y_estado, tiene_filas, hay_origen = (
                _contexto_planeador_anio_anterior(cursor, asignacion_id, usuario)
            )
            # La guardia del año, antes de escribir nada, con el estado ya leído.
            exigir_anio_editable(anio_y_estado, usuario)
            if tiene_filas:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=MENSAJE_PLANEADOR_CON_CONTENIDO,
                )
            if not hay_origen:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=MENSAJE_SIN_PLANEADOR_ANTERIOR,
                )
            filas = planeador_anual_repository.copiar_planeador_anio_anterior(
                cursor, asignacion_id, destino_id
            )
    except IntegrityError as exc:
        # Dos clics a la vez: el segundo también vio el planeador vacío.
        if exc.pgcode == errorcodes.UNIQUE_VIOLATION:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=MENSAJE_PLANEADOR_CON_CONTENIDO,
            ) from exc
        raise
    return {"message": MENSAJE_PLANEADOR_TRAIDO, "filas_copiadas": filas}
