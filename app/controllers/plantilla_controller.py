import json

from fastapi import HTTPException, status

from app.database import get_cursor
from app.schemas.plantilla import TIPOS_PLANTILLA


def _row_to_plantilla(row):
    return {
        "id": row[0],
        "tipo": row[1],
        "nombre": row[2],
        "codigo": row[3],
        "es_predefinida": row[4],
        "activa": row[5],
        "config_json": row[6] or {},
        "creado_en": row[7],
        "actualizado_en": row[8],
    }


def listar_plantillas_controller(tipo: str | None = None):
    with get_cursor() as cursor:
        if tipo:
            if tipo not in TIPOS_PLANTILLA:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"tipo invalido. Use uno de: {', '.join(sorted(TIPOS_PLANTILLA))}"
                )
            cursor.execute("""
                SELECT id, tipo, nombre, codigo, es_predefinida, activa,
                       config_json, creado_en, actualizado_en
                FROM plantilla_impresion
                WHERE tipo = %s
                ORDER BY es_predefinida DESC, nombre ASC
            """, (tipo,))
        else:
            cursor.execute("""
                SELECT id, tipo, nombre, codigo, es_predefinida, activa,
                       config_json, creado_en, actualizado_en
                FROM plantilla_impresion
                ORDER BY tipo ASC, es_predefinida DESC, nombre ASC
            """)
        rows = cursor.fetchall()

    return [_row_to_plantilla(r) for r in rows]


def obtener_plantilla_activa_controller(tipo: str):
    if tipo not in TIPOS_PLANTILLA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"tipo invalido. Use uno de: {', '.join(sorted(TIPOS_PLANTILLA))}"
        )
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, tipo, nombre, codigo, es_predefinida, activa,
                   config_json, creado_en, actualizado_en
            FROM plantilla_impresion
            WHERE tipo = %s AND activa = TRUE
            LIMIT 1
        """, (tipo,))
        row = cursor.fetchone()

        if not row:
            # Fallback: primera predefinida del tipo
            cursor.execute("""
                SELECT id, tipo, nombre, codigo, es_predefinida, activa,
                       config_json, creado_en, actualizado_en
                FROM plantilla_impresion
                WHERE tipo = %s AND es_predefinida = TRUE
                ORDER BY id ASC
                LIMIT 1
            """, (tipo,))
            row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay plantilla disponible para tipo '{tipo}'"
        )
    return _row_to_plantilla(row)


def crear_plantilla_controller(plantilla):
    if plantilla.tipo not in TIPOS_PLANTILLA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"tipo invalido. Use uno de: {', '.join(sorted(TIPOS_PLANTILLA))}"
        )
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO plantilla_impresion (tipo, nombre, es_predefinida, activa, config_json)
            VALUES (%s, %s, FALSE, FALSE, %s)
            RETURNING id
        """, (plantilla.tipo, plantilla.nombre, json.dumps(plantilla.config_json or {})))
        nuevo_id = cursor.fetchone()[0]

    return {"id": nuevo_id, "mensaje": "Plantilla creada"}


def actualizar_plantilla_controller(plantilla_id: int, datos):
    with get_cursor(commit=True) as cursor:
        # Verificar existencia y si es predefinida (no se puede renombrar/cambiar config base)
        cursor.execute("""
            SELECT es_predefinida FROM plantilla_impresion WHERE id = %s
        """, (plantilla_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        es_predefinida = row[0]
        if es_predefinida:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las plantillas predefinidas no se pueden editar. Duplica para personalizar."
            )

        campos = []
        valores = []
        if datos.nombre is not None:
            campos.append("nombre = %s")
            valores.append(datos.nombre)
        if datos.config_json is not None:
            campos.append("config_json = %s")
            valores.append(json.dumps(datos.config_json))

        if not campos:
            return {"mensaje": "Sin cambios"}

        campos.append("actualizado_en = CURRENT_TIMESTAMP")
        valores.append(plantilla_id)
        cursor.execute(
            f"UPDATE plantilla_impresion SET {', '.join(campos)} WHERE id = %s",
            tuple(valores)
        )

    return {"mensaje": "Plantilla actualizada"}


def activar_plantilla_controller(plantilla_id: int):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT tipo FROM plantilla_impresion WHERE id = %s
        """, (plantilla_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        tipo = row[0]
        # Desactivar otras del mismo tipo y activar esta. Indice unico parcial garantiza una sola activa.
        cursor.execute("""
            UPDATE plantilla_impresion SET activa = FALSE WHERE tipo = %s AND id != %s
        """, (tipo, plantilla_id))
        cursor.execute("""
            UPDATE plantilla_impresion
            SET activa = TRUE, actualizado_en = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (plantilla_id,))

    return {"mensaje": f"Plantilla activada para tipo '{tipo}'"}


def duplicar_plantilla_controller(plantilla_id: int, nuevo_nombre: str | None = None):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT tipo, nombre, config_json FROM plantilla_impresion WHERE id = %s
        """, (plantilla_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        tipo, nombre_origen, config = row
        nombre_final = nuevo_nombre or f"{nombre_origen} (copia)"

        cursor.execute("""
            INSERT INTO plantilla_impresion (tipo, nombre, es_predefinida, activa, config_json)
            VALUES (%s, %s, FALSE, FALSE, %s)
            RETURNING id
        """, (tipo, nombre_final, json.dumps(config or {})))
        nuevo_id = cursor.fetchone()[0]

    return {"id": nuevo_id, "mensaje": "Plantilla duplicada"}


def eliminar_plantilla_controller(plantilla_id: int):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT es_predefinida FROM plantilla_impresion WHERE id = %s
        """, (plantilla_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        if row[0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden eliminar plantillas predefinidas"
            )

        cursor.execute("DELETE FROM plantilla_impresion WHERE id = %s", (plantilla_id,))

    return {"mensaje": "Plantilla eliminada"}
