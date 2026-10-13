"""Entrevista de admisión, paso E1: la tabla ``admisiones``.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real del SQL
y de sus reglas se comprueba después en una rama de Neon y solo entonces se
regenera el esquema base, como exige ``docs/MIGRACIONES.md``. Diseño en
``docs/funcionalidades/ENTREVISTA_ADMISION.md``.
"""

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261013_admisiones.sql"
ESQUEMA_BASE = RAIZ / "migrations" / "base" / "20260813_esquema_base_tenant.sql"

# Lo que al matricular se copia de la admisión a la ficha del estudiante.
COPIADAS_A_ESTUDIANTES = (
    "nombre",
    "apellido",
    "tipo_documento",
    "documento_identidad",
    "fecha_nacimiento",
    "colegio_anterior",
    "anio_cursado_anterior",
    "pre_escolar_anterior",
    "ebp_anterior",
    "motivo_retiro_anterior",
    "paz_salvo_anterior",
    "ocupacion_padre",
    "ocupacion_madre",
)


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_sin_comentarios():
    return re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)


def sql_normalizado():
    return " ".join(sql_sin_comentarios().upper().split())


def definicion_tabla():
    tabla = re.search(
        r"CREATE TABLE IF NOT EXISTS admisiones \((.*?)\n\);",
        sql_sin_comentarios(),
        flags=re.DOTALL,
    )
    assert tabla is not None, "No se encontró CREATE TABLE IF NOT EXISTS admisiones"
    return tabla.group(1)


def columnas_admisiones():
    """Nombre de cada columna -> su definición, con espacios simples."""
    columnas = {}
    for linea in definicion_tabla().splitlines():
        linea = " ".join(linea.strip().rstrip(",").split())
        coincidencia = re.match(r"([a-z][a-z0-9_]*) ([A-Z].*)$", linea)
        if coincidencia:
            columnas[coincidencia.group(1)] = coincidencia.group(2)
    return columnas


def tipos_estudiantes_en_base():
    """Tipo de cada columna de ``estudiantes`` en el esquema base, escrito como
    en la migración (``character varying(100)`` -> ``VARCHAR(100)``)."""
    texto = ESQUEMA_BASE.read_text(encoding="utf-8")
    tabla = re.search(
        r"CREATE TABLE IF NOT EXISTS estudiantes \((.*?)\n\);",
        texto,
        flags=re.DOTALL,
    )
    assert tabla is not None
    tipos = {}
    for linea in tabla.group(1).splitlines():
        coincidencia = re.match(r"\s+([a-z_]+) (character varying\(\d+\)|text|date)", linea)
        if coincidencia:
            tipo = coincidencia.group(2).replace("character varying", "VARCHAR")
            tipos[coincidencia.group(1)] = tipo.upper()
    return tipos


def test_crea_la_tabla_de_admisiones_una_fila_por_aspirante():
    columnas = columnas_admisiones()

    assert columnas["id"] == "SERIAL PRIMARY KEY"
    assert columnas["anio_lectivo_id"] == "INTEGER NOT NULL"


def test_datos_del_aspirante():
    columnas = columnas_admisiones()

    assert columnas["nombre"] == "VARCHAR(100) NOT NULL"
    assert columnas["apellido"] == "VARCHAR(100) NOT NULL"
    assert columnas["tipo_documento"] == "VARCHAR(50)"
    assert columnas["documento_identidad"] == "VARCHAR(20)"
    assert columnas["fecha_nacimiento"] == "DATE"
    assert columnas["curso_id"] == "INTEGER"
    assert columnas["acudiente_nombre"] == "VARCHAR(150)"
    assert columnas["acudiente_parentesco"] == "VARCHAR(50)"
    assert columnas["acudiente_telefono"] == "VARCHAR(50)"


def test_datos_de_la_entrevista():
    columnas = columnas_admisiones()

    assert columnas["fecha_entrevista"] == "DATE"
    # Se escribe a mano (decisión del usuario, 2026-10-13): quien entrevista
    # puede no tener usuario en el sistema.
    assert columnas["entrevistador"] == "VARCHAR(150)"
    assert columnas["asistentes"] == "VARCHAR(250)"
    assert columnas["vive_con"] == "VARCHAR(250)"
    assert columnas["expectativas"] == "TEXT"
    assert columnas["observaciones"] == "TEXT"


def test_los_datos_que_se_copian_al_matricular_caben_en_la_ficha_del_estudiante():
    columnas = columnas_admisiones()
    tipos_estudiantes = tipos_estudiantes_en_base()

    for nombre in COPIADAS_A_ESTUDIANTES:
        tipo_admision = columnas[nombre].split()[0]
        assert tipo_admision == tipos_estudiantes[nombre], (
            f"{nombre}: {tipo_admision} en admisiones y "
            f"{tipos_estudiantes[nombre]} en estudiantes; la copia podría cortarse"
        )


def test_no_guarda_datos_que_puedan_discriminar():
    nombres = " ".join(columnas_admisiones())

    for prohibido in ("religion", "estado_civil", "etnia", "orientacion", "credo"):
        assert prohibido not in nombres


def test_la_autorizacion_de_datos_es_obligatoria():
    columnas = columnas_admisiones()
    texto = sql_normalizado()

    assert columnas["autoriza_datos"] == "BOOLEAN NOT NULL"
    assert columnas["autoriza_nombre"] == "VARCHAR(150) NOT NULL"
    assert "CONSTRAINT CHK_ADMISIONES_AUTORIZA CHECK (AUTORIZA_DATOS)" in texto


def test_el_resultado_empieza_pendiente_y_solo_admite_tres_valores():
    columnas = columnas_admisiones()
    texto = sql_normalizado()

    assert columnas["resultado"] == "VARCHAR(20) NOT NULL DEFAULT 'pendiente'"
    assert columnas["motivo_resultado"] == "TEXT"
    assert columnas["decidido_en"] == "TIMESTAMPTZ"
    assert (
        "CONSTRAINT CHK_ADMISIONES_RESULTADO "
        "CHECK (RESULTADO IN ('PENDIENTE', 'APROBADO', 'NO_APROBADO'))"
    ) in texto


def test_no_aprobado_exige_el_motivo():
    texto = sql_normalizado()

    assert (
        "CONSTRAINT CHK_ADMISIONES_MOTIVO_NO_APROBADO CHECK "
        "(RESULTADO <> 'NO_APROBADO' OR NULLIF(TRIM(MOTIVO_RESULTADO), '') IS NOT NULL)"
    ) in texto


def test_solo_un_aprobado_queda_enlazado_a_un_estudiante_y_una_sola_vez():
    columnas = columnas_admisiones()
    texto = sql_normalizado()

    assert columnas["estudiante_id"] == "INTEGER"
    assert "CONSTRAINT ADMISIONES_ESTUDIANTE_ID_KEY UNIQUE (ESTUDIANTE_ID)" in texto
    assert (
        "CONSTRAINT ADMISIONES_ESTUDIANTE_FKEY "
        "FOREIGN KEY (ESTUDIANTE_ID) REFERENCES ESTUDIANTES (ID)"
    ) in texto
    assert (
        "CONSTRAINT CHK_ADMISIONES_MATRICULA_APROBADA "
        "CHECK (ESTUDIANTE_ID IS NULL OR RESULTADO = 'APROBADO')"
    ) in texto


def test_la_admision_pertenece_a_un_anio_y_su_curso_es_de_ese_mismo_anio():
    texto = sql_normalizado()

    assert (
        "CONSTRAINT ADMISIONES_ANIO_LECTIVO_FKEY "
        "FOREIGN KEY (ANIO_LECTIVO_ID) REFERENCES ANIOS_LECTIVOS (ID)"
    ) in texto
    # Igual que matriculas: usa cursos_id_anio_lectivo_key UNIQUE (id, anio_lectivo_id).
    assert (
        "CONSTRAINT ADMISIONES_CURSO_ANIO_LECTIVO_FKEY "
        "FOREIGN KEY (CURSO_ID, ANIO_LECTIVO_ID) REFERENCES CURSOS (ID, ANIO_LECTIVO_ID)"
    ) in texto


def test_guarda_cuando_se_creo_y_cuando_se_cambio():
    columnas = columnas_admisiones()

    assert columnas["creado_en"] == "TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP"
    assert columnas["actualizado_en"] == "TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP"


def test_nada_se_borra_en_cascada():
    assert "ON DELETE" not in sql_normalizado()


def test_indices_para_listar_por_anio_y_no_repetir_documento_en_un_anio():
    texto = sql_normalizado()

    assert (
        "CREATE INDEX IF NOT EXISTS IDX_ADMISIONES_ANIO "
        "ON ADMISIONES (ANIO_LECTIVO_ID, RESULTADO);"
    ) in texto
    assert (
        "CREATE UNIQUE INDEX IF NOT EXISTS IDX_ADMISIONES_DOCUMENTO_POR_ANIO "
        "ON ADMISIONES (ANIO_LECTIVO_ID, DOCUMENTO_IDENTIDAD) "
        "WHERE DOCUMENTO_IDENTIDAD IS NOT NULL;"
    ) in texto


def test_es_reejecutable_sin_duplicar_estructura():
    texto = sql_normalizado()

    assert texto.count("CREATE TABLE") == 1
    assert texto.count("CREATE TABLE IF NOT EXISTS") == 1
    assert texto.count("CREATE INDEX IF NOT EXISTS") == 1
    assert texto.count("CREATE UNIQUE INDEX IF NOT EXISTS") == 1


def test_no_cambia_datos_ni_tablas_existentes():
    texto = sql_sin_comentarios().upper()

    for operacion in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP", "ALTER"):
        assert not re.search(rf"\b{operacion}\b", texto)
