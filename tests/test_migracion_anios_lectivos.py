"""La migracion A del año lectivo, fijada por sus decisiones.

Ver la fase 1 de docs/funcionalidades/ANIO_LECTIVO.md. Como el resto de
pruebas de migraciones del repo, leen el SQL: no hay PostgreSQL en CI. Que el
SQL sea valido y haga lo que dice se comprueba aplicandolo en una rama de
Neon. Lo que protegen estas pruebas son las decisiones: si alguien deshace
una, no se rompe nada visible, pero se pierde historial o se mezclan años.
"""
import re
from pathlib import Path

from app.controllers import tipos_pagos_controller


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20260930_anios_lectivos.sql"

TABLAS_CON_ANIO = {
    "cursos",
    "tipos_de_pagos",
    "matriculas",
    "pagos",
    "observador_anotaciones",
}

# Cuelgan de un curso (o de una asignacion, que cuelga de un curso): quedan
# separadas por año sin tocarlas. Es la idea central del diseño.
TABLAS_QUE_NO_SE_TOCAN = {
    "estudiantes",
    "asignaciones",
    "notas",
    "notas_detalle",
    "boletin_cabecera",
    "boletin_detalles",
    "asistencia",
    "observaciones",
    "planeador_anual",
    "plan_de_clases",
    "tipos_pagos_cursos",
    "tipos_pagos_estudiantes",
    "pagos_aplicaciones",
    "listas_seguimiento_columnas",
    "listas_seguimiento_marcas",
    "materias",
}


def sql():
    """El SQL de verdad, sin comentarios: los comentarios nombran cosas
    (DROP, NOT NULL, estudiantes.curso_id) que no son codigo."""
    texto = MIGRACION.read_text(encoding="utf-8")
    return re.sub(r"--.*$", "", texto, flags=re.MULTILINE)


def sql_normalizado():
    return re.sub(r"\s+", " ", sql()).upper()


def test_crea_la_tabla_con_los_cuatro_estados():
    texto = sql_normalizado()

    assert "CREATE TABLE IF NOT EXISTS ANIOS_LECTIVOS" in texto
    assert "CHECK (ESTADO IN ('PREPARACION', 'ACTIVO', 'CERRADO', 'REABIERTO'))" in texto


def test_la_base_de_datos_impide_dos_activos_o_dos_en_preparacion():
    texto = sql_normalizado()

    assert "ON ANIOS_LECTIVOS (ESTADO) WHERE ESTADO = 'ACTIVO'" in texto
    assert "ON ANIOS_LECTIVOS (ESTADO) WHERE ESTADO = 'PREPARACION'" in texto
    assert texto.count("CREATE UNIQUE INDEX IF NOT EXISTS IDX_ANIOS_LECTIVOS_") == 2


def test_2026_va_escrito_y_no_calculado_con_la_fecha_del_dia():
    """Todo lo existente es de 2026 (fase 0), aunque se aplique en enero."""
    texto = sql_normalizado()

    assert "VALUES (2026, 'ACTIVO', CURRENT_TIMESTAMP)" in texto
    assert "EXTRACT(YEAR" not in texto
    assert "DATE_PART" not in texto
    assert "CURRENT_DATE" not in texto


def test_agrega_el_año_exactamente_a_las_cinco_tablas_previstas():
    agregadas = set(
        re.findall(
            r"ALTER TABLE (\w+)\s+ADD COLUMN IF NOT EXISTS anio_lectivo_id",
            sql(),
            flags=re.IGNORECASE,
        )
    )

    assert agregadas == TABLAS_CON_ANIO


def test_no_altera_las_tablas_que_ya_cuelgan_de_un_curso():
    alteradas = set(
        tabla.lower()
        for tabla in re.findall(r"ALTER TABLE (\w+)", sql(), flags=re.IGNORECASE)
    )
    actualizadas = set(
        tabla.lower()
        for tabla in re.findall(r"UPDATE (\w+)\s+SET", sql(), flags=re.IGNORECASE)
    )

    assert not (alteradas & TABLAS_QUE_NO_SE_TOCAN)
    assert not (actualizadas & TABLAS_QUE_NO_SE_TOCAN)


def test_no_toca_el_curso_vigente_del_estudiante():
    """estudiantes.curso_id sigue siendo el curso del año activo."""
    assert not re.search(r"UPDATE\s+estudiantes", sql(), flags=re.IGNORECASE)


def test_las_columnas_nuevas_admiten_null_hasta_la_migracion_b():
    """El codigo viejo puede crear filas sin año entre aplicar y desplegar."""
    texto = sql_normalizado()

    assert "SET NOT NULL" not in texto
    assert not re.search(r"ANIO_LECTIVO_ID INTEGER NOT NULL", texto)


def test_no_borra_datos_ni_estructura():
    texto = sql_normalizado()

    for prohibido in ("DELETE ", "TRUNCATE", "DROP TABLE", "DROP COLUMN", "CASCADE"):
        assert prohibido not in texto, prohibido


def test_solo_quita_las_dos_reglas_de_unicidad_que_reemplaza():
    texto = sql_normalizado()

    assert re.findall(r"DROP (?:INDEX|CONSTRAINT) IF EXISTS (\w+)", texto) == [
        "IDX_CURSOS_NOMBRE_JORNADA_UNICO",
        "TIPOS_DE_PAGOS_NOMBRE_KEY",
    ]


def test_cursos_y_conceptos_se_pueden_repetir_uno_por_año():
    texto = sql_normalizado()

    assert "ON CURSOS ( ANIO_LECTIVO_ID, (UPPER(REGEXP_REPLACE(TRIM(NOMBRE)" in texto
    assert "UNIQUE (ANIO_LECTIVO_ID, NOMBRE)" in texto


def test_la_regla_de_cursos_conserva_la_expresion_original():
    """Mismo criterio de "repetido" que 20260623_admin_unicos_academicos.sql."""
    original = (RAIZ / "migrations" / "20260623_admin_unicos_academicos.sql").read_text(
        encoding="utf-8"
    )
    for fragmento in (
        "(UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g')))",
        "(LOWER(COALESCE(NULLIF(TRIM(jornada), ''), 'Mañana')))",
        "WHERE NULLIF(TRIM(COALESCE(nombre, '')), '') IS NOT NULL",
    ):
        assert fragmento in original
        assert fragmento in sql()


def test_un_freno_final_impide_que_quede_una_regla_sin_año():
    texto = sql_normalizado()

    assert "QUEDAN REGLAS DE UNICIDAD SIN AÑO LECTIVO" in texto
    assert "NOT (COLUMNA_ANIO.ATTNUM = ANY (I.INDKEY))" in texto


def test_matriculas_un_curso_por_estudiante_y_año_y_del_mismo_año():
    texto = sql_normalizado()

    assert "ON MATRICULAS (ESTUDIANTE_ID, ANIO_LECTIVO_ID)" in texto
    assert "UNIQUE (ID, ANIO_LECTIVO_ID)" in texto
    assert (
        "FOREIGN KEY (CURSO_ID, ANIO_LECTIVO_ID) REFERENCES CURSOS (ID, ANIO_LECTIVO_ID)"
        in texto
    )


def test_las_matriculas_toman_el_año_del_curso_y_no_se_duplican():
    texto = sql_normalizado()

    assert "SELECT E.ID, E.CURSO_ID, C.ANIO_LECTIVO_ID FROM ESTUDIANTES E" in texto
    assert "JOIN CURSOS C ON C.ID = E.CURSO_ID" in texto
    assert "WHERE NOT EXISTS ( SELECT 1 FROM MATRICULAS M" in texto


def test_se_detiene_si_matriculas_tiene_filas_viejas():
    texto = sql_normalizado()

    assert "MATRICULAS TIENE % FILA(S) ANTIGUAS SIN AÑO LECTIVO" in texto
    # El freno va antes de cualquier cambio.
    assert texto.index("RAISE EXCEPTION") < texto.index("CREATE TABLE")


def test_es_reejecutable():
    texto = sql_normalizado()

    assert "ADD COLUMN IF NOT EXISTS" in texto
    assert "ADD COLUMN ANIO" not in texto
    assert "ON CONFLICT (ANIO) DO NOTHING" in texto
    assert texto.count("WHERE ANIO_LECTIVO_ID IS NULL;") == 4
    # Cada ADD CONSTRAINT va dentro de un DO con su comprobacion previa.
    assert texto.count("ADD CONSTRAINT") == texto.count("FROM PG_CONSTRAINT WHERE CONNAME")
    for indice in re.findall(r"CREATE (?:UNIQUE )?INDEX (?!IF NOT EXISTS)", texto):
        raise AssertionError(f"indice sin IF NOT EXISTS: {indice}")


def test_la_respuesta_de_tipos_de_pago_no_expone_la_columna_nueva():
    """Promesa de la fase 1: invisible. Es el unico SELECT * de las tablas
    tocadas; su serializador solo copia columnas conocidas."""
    fila = {
        "id": 1,
        "nombre": "MENSUALIDAD",
        "valor": 0,
        "tipo_cobro": "mensual",
        "anio_lectivo_id": 1,
    }

    serializado = tipos_pagos_controller._serializar_tipo(
        fila, columnas_disponibles={"tipo_cobro", "anio_lectivo_id"},
    )

    assert "anio_lectivo_id" not in serializado
