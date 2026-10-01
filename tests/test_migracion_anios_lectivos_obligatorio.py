"""La migracion B del año lectivo, fijada por sus decisiones.

Ver la fase 1, punto 3, de docs/funcionalidades/ANIO_LECTIVO.md. Como las
pruebas de la migracion A, leen el SQL: no hay PostgreSQL en CI. Que el SQL
sea valido y haga lo que dice se comprueba aplicandolo en una rama de Neon.

La ultima prueba no lee la migracion sino el codigo: es la condicion que hace
segura a esta migracion. Despues de B, un INSERT de app/ que no escriba el año
en una de estas tablas fallaria en produccion.
"""
import re
from pathlib import Path

from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261001_anios_lectivos_obligatorio.sql"

TABLAS_CON_ANIO = {
    "cursos",
    "tipos_de_pagos",
    "matriculas",
    "pagos",
    "observador_anotaciones",
}

# Las que el codigo viejo podia crear sin año entre la migracion A y el
# despliegue. `matriculas` no: el codigo viejo no escribia en ella.
TABLAS_QUE_SE_RELLENAN = TABLAS_CON_ANIO - {"matriculas"}

# Un UPDATE de una sentencia, no el DO UPDATE del ON CONFLICT.
ACTUALIZACION = r"(?<!DO )UPDATE (\w+) SET"


def sql():
    """El SQL de verdad, sin comentarios: los comentarios nombran cosas
    (NOT NULL, `estudiantes.curso_id`, scripts) que no son codigo."""
    texto = MIGRACION.read_text(encoding="utf-8")
    return re.sub(r"--.*$", "", texto, flags=re.MULTILINE)


def normalizar(texto):
    return re.sub(r"\s+", " ", texto).strip().upper()


def sql_normalizado():
    return normalizar(sql())


def test_vuelve_obligatorio_el_año_exactamente_en_las_cinco_tablas():
    texto = sql_normalizado()

    obligatorias = re.findall(r"ALTER TABLE (\w+) ALTER COLUMN (\w+) SET NOT NULL", texto)

    assert sorted(obligatorias) == sorted(
        (tabla.upper(), "ANIO_LECTIVO_ID") for tabla in TABLAS_CON_ANIO
    )
    # Ninguna otra columna se vuelve obligatoria.
    assert texto.count("SET NOT NULL") == len(TABLAS_CON_ANIO)


def test_rellena_con_el_mismo_año_que_escribe_el_codigo():
    """Lo que quedo sin año recibe lo que el codigo nuevo habria escrito."""
    anio_activo = re.escape(normalizar(ANIO_ACTIVO_ID_SQL))

    rellenadas = re.findall(
        rf"UPDATE (\w+) SET ANIO_LECTIVO_ID = {anio_activo} WHERE ANIO_LECTIVO_ID IS NULL;",
        sql_normalizado(),
    )

    assert sorted(rellenadas) == sorted(tabla.upper() for tabla in TABLAS_QUE_SE_RELLENAN)


def test_un_colegio_sin_año_activo_recibe_2026_escrito_y_no_calculado():
    """Un colegio dado de alta entre la migracion A y el despliegue: el
    esquema base trae la tabla pero no la fila del año."""
    texto = sql_normalizado()

    assert (
        "INSERT INTO ANIOS_LECTIVOS (ANIO, ESTADO, ACTIVADO_EN) "
        "SELECT 2026, 'ACTIVO', CURRENT_TIMESTAMP "
        "WHERE NOT EXISTS (SELECT 1 FROM ANIOS_LECTIVOS WHERE ESTADO = 'ACTIVO') "
        "ON CONFLICT (ANIO) DO NOTHING;"
    ) in texto
    for calculado in ("EXTRACT(YEAR", "DATE_PART", "CURRENT_DATE", "NOW()"):
        assert calculado not in texto, calculado


def test_el_año_activo_se_asegura_antes_de_rellenar():
    texto = sql_normalizado()

    assert texto.index("INSERT INTO ANIOS_LECTIVOS") < re.search(ACTUALIZACION, texto).start()


def test_pone_al_dia_las_matriculas_del_año_activo_con_el_curso_del_estudiante():
    texto = sql_normalizado()

    assert (
        "INSERT INTO MATRICULAS (ESTUDIANTE_ID, CURSO_ID, ANIO_LECTIVO_ID) "
        "SELECT E.ID, E.CURSO_ID, C.ANIO_LECTIVO_ID "
        "FROM ESTUDIANTES E "
        "JOIN CURSOS C ON C.ID = E.CURSO_ID "
        "JOIN ANIOS_LECTIVOS AL ON AL.ID = C.ANIO_LECTIVO_ID "
        "WHERE AL.ESTADO = 'ACTIVO' "
        "ON CONFLICT (ESTUDIANTE_ID, ANIO_LECTIVO_ID) "
        "DO UPDATE SET CURSO_ID = EXCLUDED.CURSO_ID "
        "WHERE MATRICULAS.CURSO_ID IS DISTINCT FROM EXCLUDED.CURSO_ID;"
    ) in texto


def test_las_matriculas_se_ponen_al_dia_despues_de_dar_año_a_los_cursos():
    """Un curso creado en la ventana no tenia año: sus estudiantes solo se
    sincronizan si el curso ya lo tiene."""
    texto = sql_normalizado()

    assert texto.index("UPDATE CURSOS SET") < texto.index("INSERT INTO MATRICULAS")


def test_el_freno_final_es_la_consulta_de_control_del_documento():
    """La regla del curso vigente: debe dar 0 filas en todo momento. Se
    revisa despues de la puesta al dia, no antes."""
    texto = sql_normalizado()
    control = (
        "FROM ESTUDIANTES E LEFT JOIN MATRICULAS M ON M.ESTUDIANTE_ID = E.ID "
        "AND M.ANIO_LECTIVO_ID = (SELECT ID FROM ANIOS_LECTIVOS WHERE ESTADO = 'ACTIVO') "
        "WHERE E.CURSO_ID IS DISTINCT FROM M.CURSO_ID;"
    )

    assert control in texto
    assert texto.index("INSERT INTO MATRICULAS") < texto.index(control)


def test_tres_frenos_detienen_el_tenant_si_algo_no_cuadra():
    texto = sql_normalizado()

    assert texto.count("RAISE EXCEPTION") == 3
    assert "MATRICULAS TIENE % FILA(S) SIN AÑO LECTIVO" in texto
    assert "NO HAY AÑO LECTIVO ACTIVO Y NO SE PUDO CREAR 2026" in texto
    assert "CON UN CURSO DISTINTO AL DE SU MATRICULA DEL AÑO ACTIVO" in texto


def test_no_borra_nada_ni_escribe_el_curso_vigente():
    """Nunca borra matriculas, y `estudiantes.curso_id` no lo escribe una
    migracion: en la fase 1 lo edita el formulario de estudiantes."""
    texto = sql_normalizado()

    for prohibido in ("DELETE ", "TRUNCATE", "DROP ", "CASCADE", "UPDATE ESTUDIANTES"):
        assert prohibido not in texto, prohibido


def test_solo_modifica_las_tablas_del_año_y_no_cambia_la_estructura():
    """Ni tablas, ni indices, ni reglas nuevas: rellenos y NOT NULL."""
    texto = sql_normalizado()

    modificadas = set(
        re.findall(r"(?:(?<!DO )UPDATE|ALTER TABLE|INSERT INTO) (\w+)", texto)
    )

    assert modificadas == {tabla.upper() for tabla in TABLAS_CON_ANIO | {"anios_lectivos"}}
    for estructura in ("CREATE ", "ADD CONSTRAINT", "ADD COLUMN"):
        assert estructura not in texto, estructura


def test_es_reejecutable():
    texto = sql_normalizado()

    assert "WHERE NOT EXISTS (SELECT 1 FROM ANIOS_LECTIVOS WHERE ESTADO = 'ACTIVO')" in texto
    assert "ON CONFLICT (ANIO) DO NOTHING" in texto
    # Cada relleno solo toca filas sin año.
    actualizaciones = [m.group(0) for m in re.finditer(rf"{ACTUALIZACION} [^;]*;", texto)]
    assert len(actualizaciones) == len(TABLAS_QUE_SE_RELLENAN)
    assert all(a.endswith("WHERE ANIO_LECTIVO_ID IS NULL;") for a in actualizaciones)
    # La puesta al dia no reescribe las matriculas que ya coinciden.
    assert "WHERE MATRICULAS.CURSO_ID IS DISTINCT FROM EXCLUDED.CURSO_ID" in texto


# ---------------------------------------------------------------------------
# Lo que hace segura a la migracion: el codigo ya escribe el año.
# ---------------------------------------------------------------------------

INSERCION = re.compile(
    r"INSERT\s+INTO\s+(cursos|tipos_de_pagos|pagos|observador_anotaciones|matriculas)\b"
    r"(\s*\(([^)]*)\))?",
    flags=re.IGNORECASE,
)

# Las que existen desde la fase 1, punto 2. Si la busqueda dejara de
# encontrarlas, la prueba pasaria sin revisar nada.
INSERCIONES_CONOCIDAS = {
    ("app/controllers/curso_controller.py", "cursos"),
    ("app/controllers/tipos_pagos_controller.py", "tipos_de_pagos"),
    ("app/repositories/pagos_repository.py", "pagos"),
    ("app/repositories/observador_repository.py", "observador_anotaciones"),
    ("app/repositories/anios_lectivos_repository.py", "matriculas"),
}


def inserciones_de_app():
    for archivo in sorted((RAIZ / "app").rglob("*.py")):
        relativo = archivo.relative_to(RAIZ).as_posix()
        for insercion in INSERCION.finditer(archivo.read_text(encoding="utf-8")):
            yield relativo, insercion.group(1).lower(), insercion.group(3)


def test_todo_insert_de_app_en_estas_tablas_escribe_el_año():
    """Despues de B, un INSERT sin año en estas tablas fallaria en produccion."""
    inserciones = list(inserciones_de_app())

    assert INSERCIONES_CONOCIDAS <= {(archivo, tabla) for archivo, tabla, _ in inserciones}
    for archivo, tabla, columnas in inserciones:
        assert columnas is not None, f"{archivo}: INSERT en {tabla} sin lista de columnas"
        assert "anio_lectivo_id" in columnas.lower(), (
            f"{archivo}: INSERT en {tabla} sin anio_lectivo_id"
        )
