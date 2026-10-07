import logging

from app.database import get_connection
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL, condicion_anio
from app.services.anio_lectivo import (
    AnioLectivoInexistenteError,
    AnioLectivoNoEditableError,
    exigir_anio_editable_para_admin,
    exigir_anio_lectivo,
    exigir_concepto_editable_para_admin,
)

logger = logging.getLogger(__name__)

# Las siete escrituras distinguen sus resultados de dominio de los fallos
# inesperados: los primeros conservan sus sentinelas o excepciones especificas y
# los segundos se registran, revierten y se propagan para que la frontera HTTP
# los exponga como errores internos.


class TipoPagoDuplicadoError(Exception):
    """Se lanza cuando ya existe un tipo de pago con el mismo nombre."""


class TipoPagoInfraestructuraError(RuntimeError):
    """Encapsula un fallo inesperado sin exponer detalles internos por HTTP."""


class CursoDeOtroAnioError(Exception):
    """Se lanza al poner precio a un concepto en un curso de otro año lectivo."""

# =============================================================================
# CRUD básico (mantener compatibles las llamadas de los flujos existentes)
# =============================================================================

def crear_tipo_pago(nombre, valor=0, anio_lectivo_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        nombre_limpio = (nombre or "").strip()
        if anio_lectivo_id is not None:
            anio = exigir_anio_lectivo(cursor, anio_lectivo_id)
            exigir_anio_editable_para_admin((anio[1], anio[2]))
        # Fase 3 del año lectivo: el nombre se repite una vez por año, como el
        # indice unico de la migracion A. El concepto se compara con el año
        # pedido (o el activo si se omitió).
        if anio_lectivo_id is None:
            cursor.execute(
                "SELECT id FROM tipos_de_pagos WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))"
                f" AND anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}",
                (nombre_limpio,),
            )
        else:
            cursor.execute(
                "SELECT id FROM tipos_de_pagos WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))"
                " AND anio_lectivo_id = %s",
                (nombre_limpio, anio_lectivo_id),
            )
        if cursor.fetchone():
            raise TipoPagoDuplicadoError(f"Ya existe un tipo de pago llamado '{nombre_limpio}'.")

        if anio_lectivo_id is None:
            # Camino anterior, conservado literalmente: nace en el año activo.
            cursor.execute(
                f'INSERT INTO tipos_de_pagos (nombre, valor, anio_lectivo_id) VALUES (%s, %s, {ANIO_ACTIVO_ID_SQL}) RETURNING id',
                (nombre, valor),
            )
        else:
            cursor.execute(
                'INSERT INTO tipos_de_pagos (nombre, valor, anio_lectivo_id) VALUES (%s, %s, %s) RETURNING id',
                (nombre, valor, anio_lectivo_id),
            )
        data = cursor.fetchone()[0]
        conn.commit()
        return {'id': data, 'nombre': nombre, 'valor': valor}
    except (
        TipoPagoDuplicadoError,
        AnioLectivoInexistenteError,
        AnioLectivoNoEditableError,
    ):
        conn.rollback()
        raise
    except Exception as exc:
        logger.exception("Fallo inesperado al crear el tipo de pago")
        conn.rollback()
        raise TipoPagoInfraestructuraError from exc
    finally:
        cursor.close()
        conn.close()

def listar_tipos_pagos(anio_lectivo_id=None):
    """Conceptos de un año; sin `anio_lectivo_id`, del activo (decision 17)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        condicion, params = condicion_anio("anio_lectivo_id", anio_lectivo_id)
        cursor.execute(
            f'SELECT id, nombre, valor FROM tipos_de_pagos WHERE {condicion} ORDER BY nombre',
            params or None,
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return [{'id': r[0], 'nombre': r[1], 'valor': float(r[2]) if r[2] is not None else 0} for r in rows]

def actualizar_tipo_pago(id, nombre, valor=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_concepto_editable_para_admin(cursor, id)
        nombre_limpio = (nombre or "").strip()
        # Fase 3 del año lectivo: se compara con los conceptos del mismo año
        # que el que se edita.
        cursor.execute(
            """
            SELECT id
            FROM tipos_de_pagos
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
              AND id <> %s
              AND anio_lectivo_id = (SELECT anio_lectivo_id FROM tipos_de_pagos WHERE id = %s)
            """,
            (nombre_limpio, id, id),
        )
        if cursor.fetchone():
            raise TipoPagoDuplicadoError(f"Ya existe un tipo de pago llamado '{nombre_limpio}'.")

        cursor.execute('UPDATE tipos_de_pagos SET nombre = %s, valor = %s WHERE id = %s RETURNING id', (nombre, valor, id))
        if cursor.fetchone():
            conn.commit()
            return True
        return False
    except (TipoPagoDuplicadoError, AnioLectivoNoEditableError):
        conn.rollback()
        raise
    except Exception as exc:
        logger.exception("Fallo inesperado al actualizar el tipo de pago %s", id)
        conn.rollback()
        raise TipoPagoInfraestructuraError from exc
    finally:
        cursor.close()
        conn.close()

def eliminar_tipo_pago(id):
    return {
        "error": (
            "Los tipos de pago no se eliminan fisicamente. "
            "Desactivalos desde la configuracion para conservar historial de cobros."
        )
    }


# =============================================================================
# Configuración financiera avanzada
# =============================================================================

# Columnas avanzadas que pueden estar en la tabla `tipos_de_pagos` después de
# aplicar la migración 20260517_tipos_pagos_avanzado.sql. Si la migración no se
# ha ejecutado, los SELECT detectan la ausencia y devuelven defaults.
_ADVANCED_COLUMNS = [
    "descripcion",
    "tipo_cobro",
    "fecha_limite",
    "dia_limite_mes",
    "dias_gracia",
    "mora_tipo",
    "mora_valor",
    "mes_inicial",
    "mes_final",
    "frecuencia_meses",
    "generacion_automatica",
    "activo",
]

_DEFAULTS = {
    "descripcion": None,
    "tipo_cobro": "unico",
    "fecha_limite": None,
    "dia_limite_mes": None,
    "dias_gracia": 0,
    "mora_tipo": None,
    "mora_valor": 0,
    "mes_inicial": None,
    "mes_final": 12,
    "frecuencia_meses": 1,
    "generacion_automatica": False,
    "activo": True,
}


def _columnas_existentes(cursor, tabla):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ANY (current_schemas(false)) AND table_name = %s
        """,
        (tabla,),
    )
    result = set()
    for row in cursor.fetchall():
        # Compatible con cursor normal (tuple) y RealDictCursor (dict)
        if isinstance(row, dict):
            result.add(row["column_name"])
        else:
            result.add(row[0])
    return result


def _serializar_tipo(row, columnas_disponibles):
    """Convierte una fila SELECT * en dict con defaults para columnas ausentes."""
    base = {
        "id": row["id"],
        "nombre": row["nombre"],
        "valor": float(row["valor"]) if row.get("valor") is not None else 0,
    }
    for col in _ADVANCED_COLUMNS:
        if col in columnas_disponibles and col in row:
            value = row[col]
            if col == "mora_valor" and value is not None:
                value = float(value)
            if col == "fecha_limite" and value is not None:
                value = value.isoformat()
            base[col] = value if value is not None else _DEFAULTS[col]
        else:
            base[col] = _DEFAULTS[col]
    return base


def obtener_tipo_pago(id):
    """Retorna un tipo de pago con su configuración avanzada (o None)."""
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        columnas = _columnas_existentes(cursor, "tipos_de_pagos")
        cursor.execute("SELECT * FROM tipos_de_pagos WHERE id = %s", (id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _serializar_tipo(row, columnas)
    finally:
        cursor.close()
        conn.close()


def listar_tipos_pagos_detallado(anio_lectivo_id=None):
    """Lista los tipos de pago de un año con configuración avanzada y cursos asignados.

    Sin `anio_lectivo_id`, los del año activo (decision 17).
    """
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        columnas = _columnas_existentes(cursor, "tipos_de_pagos")
        condicion, params = condicion_anio("anio_lectivo_id", anio_lectivo_id)
        cursor.execute(
            f"SELECT * FROM tipos_de_pagos WHERE {condicion} ORDER BY nombre",
            params or None,
        )
        tipos = [_serializar_tipo(r, columnas) for r in cursor.fetchall()]

        if not tipos:
            return []

        if "tipos_pagos_cursos" in {t for t in _table_names(cursor)}:
            cursor.execute(
                """
                SELECT tpc.tipo_pago_id, tpc.curso_id, tpc.valor, tpc.activo,
                       c.nombre AS curso_nombre
                FROM tipos_pagos_cursos tpc
                JOIN cursos c ON c.id = tpc.curso_id
                ORDER BY c.nombre
                """
            )
            por_tipo = {}
            for r in cursor.fetchall():
                por_tipo.setdefault(r["tipo_pago_id"], []).append(
                    {
                        "curso_id": r["curso_id"],
                        "curso_nombre": r["curso_nombre"],
                        "valor": float(r["valor"]) if r["valor"] is not None else 0,
                        "activo": r["activo"],
                    }
                )
            for tipo in tipos:
                tipo["cursos"] = por_tipo.get(tipo["id"], [])
        else:
            for tipo in tipos:
                tipo["cursos"] = []

        return tipos
    finally:
        cursor.close()
        conn.close()


def _table_names(cursor):
    cursor.execute(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = ANY (current_schemas(false))
        """
    )
    result = set()
    for row in cursor.fetchall():
        if isinstance(row, dict):
            result.add(row["table_name"])
        else:
            result.add(row[0])
    return result


class MigracionPendienteError(Exception):
    """Se lanza cuando falta una migración requerida por la configuración."""


class ConfiguracionTipoPagoInvalidaError(ValueError):
    """Se lanza cuando la combinación efectiva de meses no es válida."""


def _validar_rango_meses(cursor, id, config, columnas):
    if not ({"tipo_cobro", "mes_inicial", "mes_final"} & config.keys()):
        return

    columnas_rango = [
        columna
        for columna in ("tipo_cobro", "mes_inicial", "mes_final")
        if columna in columnas
    ]
    if not columnas_rango:
        return

    cursor.execute(
        f"SELECT {', '.join(columnas_rango)} "
        "FROM tipos_de_pagos WHERE id = %s FOR UPDATE",
        (id,),
    )
    fila = cursor.fetchone()
    if not fila:
        return

    actuales = dict(zip(columnas_rango, fila))
    tipo_cobro = config.get("tipo_cobro", actuales.get("tipo_cobro", "unico"))
    if str(tipo_cobro or "").strip().lower() != "mensual":
        return

    mes_inicial = config.get("mes_inicial", actuales.get("mes_inicial"))
    mes_final = config.get("mes_final", actuales.get("mes_final", 12))
    mes_final = 12 if mes_final is None else int(mes_final)

    if mes_inicial is not None and mes_final < int(mes_inicial):
        raise ConfiguracionTipoPagoInvalidaError(
            "El mes final no puede ser anterior al mes inicial."
        )


def actualizar_configuracion_tipo_pago(id, config):
    """Actualiza únicamente las columnas avanzadas de un tipo de pago.

    `config` es un dict; sólo se aplican las claves presentes y soportadas por
    el schema. NO toca `nombre` ni `valor` (esos los maneja `actualizar_tipo_pago`).

    Levanta `MigracionPendienteError` si ninguna columna avanzada existe aún
    (caso típico: la migración no se aplicó). Devuelve True/False en otros casos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_concepto_editable_para_admin(cursor, id)
        columnas = _columnas_existentes(cursor, "tipos_de_pagos")

        # Si NO existe NINGUNA columna avanzada, la migración está pendiente.
        if not any(col in columnas for col in _ADVANCED_COLUMNS):
            raise MigracionPendienteError(
                "Las columnas avanzadas de 'tipos_de_pagos' no existen. "
                "Ejecuta: python scripts/apply_tipos_pagos_avanzado_migration.py"
            )

        if "mes_final" in config and "mes_final" not in columnas:
            raise MigracionPendienteError(
                "La columna 'mes_final' de 'tipos_de_pagos' no existe. "
                "Ejecuta: python apply_migration.py "
                "migrations/20260910_tipos_pagos_mes_final.sql"
            )

        _validar_rango_meses(cursor, id, config, columnas)

        sets = []
        params = []
        for col in _ADVANCED_COLUMNS:
            if col in config and col in columnas:
                sets.append(f"{col} = %s")
                params.append(config[col])
        if "updated_at" in columnas:
            sets.append("updated_at = CURRENT_TIMESTAMP")

        if not sets:
            return False

        params.append(id)
        cursor.execute(
            f"UPDATE tipos_de_pagos SET {', '.join(sets)} WHERE id = %s RETURNING id",
            params,
        )
        if cursor.fetchone():
            conn.commit()
            return True
        return False
    except (MigracionPendienteError, ConfiguracionTipoPagoInvalidaError, AnioLectivoNoEditableError):
        conn.rollback()
        raise
    except Exception as exc:
        logger.exception(
            "Fallo inesperado al actualizar la configuracion del tipo de pago %s", id
        )
        conn.rollback()
        raise TipoPagoInfraestructuraError from exc
    finally:
        cursor.close()
        conn.close()


# =============================================================================
# Asignación de tipos de pago a cursos (tabla puente)
# =============================================================================

def _consultar_cursos_asignados(cursor, tipo_pago_id):
    """Lee las asignaciones con el cursor que ya abrio quien llama.

    Extraida para que `upsert_cursos_asignados` pueda devolver el estado sin
    abrir una segunda conexion. Exige un cursor tipo dict, como el que usan sus
    dos consumidores.
    """
    # Si la tabla puente todavía no existe (migración no aplicada),
    # devolvemos lista vacía en lugar de explotar.
    if "tipos_pagos_cursos" not in _table_names(cursor):
        return []

    cursor.execute(
            """
            SELECT tpc.id, tpc.tipo_pago_id, tpc.curso_id, tpc.valor, tpc.activo,
                   c.nombre AS curso_nombre
            FROM tipos_pagos_cursos tpc
            JOIN cursos c ON c.id = tpc.curso_id
            WHERE tpc.tipo_pago_id = %s
            ORDER BY c.nombre
            """,
        (tipo_pago_id,),
    )
    return [
        {
            "id": r["id"],
            "tipo_pago_id": r["tipo_pago_id"],
            "curso_id": r["curso_id"],
            "curso_nombre": r["curso_nombre"],
            "valor": float(r["valor"]) if r["valor"] is not None else 0,
            "activo": r["activo"],
        }
        for r in cursor.fetchall()
    ]


def listar_cursos_asignados(tipo_pago_id):
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        return _consultar_cursos_asignados(cursor, tipo_pago_id)
    finally:
        cursor.close()
        conn.close()


def upsert_cursos_asignados(tipo_pago_id, asignaciones):
    """Upsert masivo de cursos asignados a un tipo de pago.

    `asignaciones`: lista de {curso_id, valor, activo?}
    Reemplaza el estado: cursos no incluidos se eliminan.

    Usa un cursor tipo dict porque devuelve el estado releyendolo con el mismo
    cursor, antes de confirmar. Antes abria una segunda conexion despues del
    `commit`: las dos se solapaban y, si esa relectura fallaba, la ruta
    respondia 400 sobre una escritura ya guardada.
    """
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_concepto_editable_para_admin(cursor, tipo_pago_id)
        curso_ids = [a["curso_id"] for a in asignaciones]

        # Una sola consulta responde dos cosas: si el concepto existe y que
        # cursos de los pedidos son de otro año. Fase 3 del año lectivo: el
        # precio de un concepto de 2027 solo se pone en cursos de 2027 (ver
        # "tipos_de_pagos.anio_lectivo_id" en docs/funcionalidades/ANIO_LECTIVO.md).
        cursor.execute(
            """
            SELECT ARRAY(
                SELECT c.nombre
                FROM cursos c
                WHERE c.id = ANY(%s::int[])
                  AND c.anio_lectivo_id <> tp.anio_lectivo_id
                ORDER BY c.nombre
            ) AS cursos_de_otro_anio
            FROM tipos_de_pagos tp
            WHERE tp.id = %s
            """,
            (curso_ids, tipo_pago_id),
        )
        concepto = cursor.fetchone()
        if not concepto:
            return None
        if concepto["cursos_de_otro_anio"]:
            raise CursoDeOtroAnioError(
                "Estos cursos no son del año lectivo del concepto: "
                f"{', '.join(concepto['cursos_de_otro_anio'])}."
            )

        if curso_ids:
            cursor.execute(
                "DELETE FROM tipos_pagos_cursos WHERE tipo_pago_id = %s AND curso_id <> ALL(%s)",
                (tipo_pago_id, curso_ids),
            )
        else:
            cursor.execute(
                "DELETE FROM tipos_pagos_cursos WHERE tipo_pago_id = %s",
                (tipo_pago_id,),
            )

        for a in asignaciones:
            cursor.execute(
                """
                INSERT INTO tipos_pagos_cursos (tipo_pago_id, curso_id, valor, activo)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tipo_pago_id, curso_id)
                DO UPDATE SET
                    valor = EXCLUDED.valor,
                    activo = EXCLUDED.activo,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    tipo_pago_id,
                    a["curso_id"],
                    a.get("valor", 0) or 0,
                    a.get("activo", True),
                ),
            )

        asignados = _consultar_cursos_asignados(cursor, tipo_pago_id)
        conn.commit()
        return asignados
    except (CursoDeOtroAnioError, AnioLectivoNoEditableError):
        conn.rollback()
        raise
    except Exception as exc:
        logger.exception(
            "Fallo inesperado al asignar cursos al tipo de pago %s", tipo_pago_id
        )
        conn.rollback()
        raise TipoPagoInfraestructuraError from exc
    finally:
        cursor.close()
        conn.close()


def eliminar_curso_asignado(tipo_pago_id, curso_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_concepto_editable_para_admin(cursor, tipo_pago_id)
        cursor.execute(
            "DELETE FROM tipos_pagos_cursos WHERE tipo_pago_id = %s AND curso_id = %s RETURNING id",
            (tipo_pago_id, curso_id),
        )
        if cursor.fetchone():
            conn.commit()
            return True
        return False
    except AnioLectivoNoEditableError:
        conn.rollback()
        raise
    except Exception as exc:
        logger.exception(
            "Fallo inesperado al desasignar el curso %s del tipo de pago %s",
            curso_id,
            tipo_pago_id,
        )
        conn.rollback()
        raise TipoPagoInfraestructuraError from exc
    finally:
        cursor.close()
        conn.close()


# =============================================================================
# Valores personalizados por estudiante
# =============================================================================

def _exigir_tabla_valores_estudiantes(cursor):
    if "tipos_pagos_estudiantes" not in _table_names(cursor):
        raise MigracionPendienteError(
            "La tabla 'tipos_pagos_estudiantes' no existe. "
            "Ejecuta la migracion 20260713_tipos_pagos_estudiantes.sql"
        )


def _consultar_valores_personalizados(
    cursor, estudiante_id, anio_lectivo_id=None
):
    """Lee los valores personalizados con el cursor que ya abrio quien llama.

    Extraida por el mismo motivo que `_consultar_cursos_asignados`. Exige un
    cursor tipo dict.
    """
    _exigir_tabla_valores_estudiantes(cursor)
    filtro_anio, params_anio = condicion_anio(
        "t.anio_lectivo_id", anio_lectivo_id
    )
    cursor.execute(
            f"""
            SELECT
                tpe.id,
                tpe.tipo_pago_id,
                tpe.estudiante_id,
                tpe.valor,
                tpe.motivo,
                tpe.activo,
                tpe.created_at,
                tpe.updated_at,
                t.nombre AS tipo_pago_nombre,
                t.valor AS valor_base,
                tpc.valor AS valor_curso
            FROM tipos_pagos_estudiantes tpe
            JOIN tipos_de_pagos t ON t.id = tpe.tipo_pago_id
            JOIN matriculas m
                ON m.estudiante_id = tpe.estudiante_id
               AND m.anio_lectivo_id = t.anio_lectivo_id
            LEFT JOIN tipos_pagos_cursos tpc
                ON tpc.tipo_pago_id = tpe.tipo_pago_id
               AND tpc.curso_id = m.curso_id
               AND tpc.activo = TRUE
            WHERE tpe.estudiante_id = %s
              AND tpe.activo = TRUE
              AND {filtro_anio}
            ORDER BY t.nombre
            """,
        (estudiante_id, *params_anio),
    )
    return [
        {
            "id": r["id"],
            "tipo_pago_id": r["tipo_pago_id"],
            "estudiante_id": r["estudiante_id"],
            "tipo_pago_nombre": r["tipo_pago_nombre"],
            "valor": float(r["valor"] or 0),
            "valor_base": float(r["valor_base"] or 0),
            "valor_curso": float(r["valor_curso"] or 0) if r["valor_curso"] is not None else None,
            "motivo": r["motivo"] or "",
            "activo": r["activo"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
        }
        for r in cursor.fetchall()
    ]


def listar_valores_personalizados_estudiante(
    estudiante_id, anio_lectivo_id=None
):
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        return _consultar_valores_personalizados(
            cursor, estudiante_id, anio_lectivo_id=anio_lectivo_id
        )
    finally:
        cursor.close()
        conn.close()


def upsert_valor_personalizado_estudiante(
    estudiante_id,
    tipo_pago_id,
    valor,
    motivo=None,
    activo=True,
):
    """Igual que `upsert_cursos_asignados`: relee con el mismo cursor y solo
    despues confirma, en vez de abrir una segunda conexion tras el `commit`."""
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_concepto_editable_para_admin(cursor, tipo_pago_id)
        _exigir_tabla_valores_estudiantes(cursor)

        cursor.execute(
            """
            SELECT tp.anio_lectivo_id, m.curso_id, e.id AS estudiante_id
            FROM tipos_de_pagos tp
            LEFT JOIN estudiantes e ON e.id = %s
            LEFT JOIN matriculas m
              ON m.estudiante_id = e.id
             AND m.anio_lectivo_id = tp.anio_lectivo_id
            WHERE tp.id = %s
            """,
            (estudiante_id, tipo_pago_id),
        )
        contexto = cursor.fetchone()
        if not contexto:
            raise ValueError("Tipo de pago no encontrado.")
        if isinstance(contexto, dict):
            anio_lectivo_id = contexto["anio_lectivo_id"]
            curso_id = contexto["curso_id"]
            estudiante_encontrado = contexto["estudiante_id"]
        else:
            anio_lectivo_id, curso_id, estudiante_encontrado = contexto
        if estudiante_encontrado is None:
            raise ValueError("Estudiante no encontrado.")
        if curso_id is None:
            raise ValueError(
                "El estudiante no tiene matrícula en el año del concepto."
            )

        if "tipos_pagos_cursos" in _table_names(cursor):
            cursor.execute(
                """
                SELECT 1
                FROM tipos_pagos_cursos
                WHERE tipo_pago_id = %s
                  AND curso_id = %s
                  AND activo = TRUE
                """,
                (tipo_pago_id, curso_id),
            )
            if not cursor.fetchone():
                raise ValueError(
                    "Este concepto no esta asignado al curso del estudiante."
                )

        cursor.execute(
            """
            INSERT INTO tipos_pagos_estudiantes
                (tipo_pago_id, estudiante_id, valor, motivo, activo)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (tipo_pago_id, estudiante_id)
            DO UPDATE SET
                valor = EXCLUDED.valor,
                motivo = EXCLUDED.motivo,
                activo = EXCLUDED.activo,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                tipo_pago_id,
                estudiante_id,
                valor or 0,
                (motivo or "").strip() or None,
                activo,
            ),
        )
        cursor.fetchone()
        valores = _consultar_valores_personalizados(
            cursor, estudiante_id, anio_lectivo_id=anio_lectivo_id
        )
        conn.commit()
        return valores
    except (MigracionPendienteError, ValueError, AnioLectivoNoEditableError):
        conn.rollback()
        raise
    except Exception as exc:
        logger.exception(
            "Fallo inesperado al guardar el valor personalizado del tipo de pago %s "
            "para el estudiante %s",
            tipo_pago_id,
            estudiante_id,
        )
        conn.rollback()
        raise TipoPagoInfraestructuraError from exc
    finally:
        cursor.close()
        conn.close()


def eliminar_valor_personalizado_estudiante(estudiante_id, tipo_pago_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_concepto_editable_para_admin(cursor, tipo_pago_id)
        _exigir_tabla_valores_estudiantes(cursor)
        cursor.execute(
            """
            UPDATE tipos_pagos_estudiantes
            SET activo = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE estudiante_id = %s
              AND tipo_pago_id = %s
              AND activo = TRUE
            RETURNING id
            """,
            (estudiante_id, tipo_pago_id),
        )
        if cursor.fetchone():
            conn.commit()
            return True
        conn.rollback()
        return False
    except (MigracionPendienteError, AnioLectivoNoEditableError):
        conn.rollback()
        raise
    except Exception as exc:
        logger.exception(
            "Fallo inesperado al eliminar el valor personalizado del tipo de pago %s "
            "del estudiante %s",
            tipo_pago_id,
            estudiante_id,
        )
        conn.rollback()
        raise TipoPagoInfraestructuraError from exc
    finally:
        cursor.close()
        conn.close()
