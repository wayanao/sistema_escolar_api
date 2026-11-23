"""Porcentajes por tipo de nota, paso B1: lo que no debe cambiar sin porcentajes.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, "Avance del paso B0" (QB3,
QB4 y PB5 a PB7). Se escribio y se corrio **antes** de tocar el codigo de la
parte B, contra el programa de hoy, y paso. Despues de B2 tiene que seguir
pasando igual: sin porcentajes activos, cada lugar que calcula la nota de un
periodo da lo de hoy, con sus diferencias (QB4).

El cursor responde segun un fragmento del SQL y, a cualquier otra consulta,
"nada". Asi, una consulta nueva de B2 que lea porcentajes y no encuentre
ninguno no rompe estas pruebas: es justo el caso "sin porcentajes".

Lo que ya fijaban otros archivos no se repite aqui:

- los conteos de consultas y de conexiones: `test_boletin_caracterizacion.py`
  y `test_dashboard_caracterizacion.py`;
- que el reporte parcial no redondea y deja fuera caritas y ceros:
  `test_boletin_caracterizacion.py`;
- la respuesta de los dos rankings: `test_dashboard_controlador.py`;
- la planilla sin parametro, guardar una nota y borrar un tipo:
  `test_subnotas_planilla_caracterizacion.py`.
"""

from contextlib import contextmanager
from decimal import Decimal

import pytest

from app.controllers import (
    boletin_controller,
    planilla_excel_controller,
)
from app.core.nivel_academico import NOMBRE_MATERIA_ASISTENCIA_JORNADA
from app.repositories import boletin_repository, dashboard_repository


ADMIN = {"id": 1, "rol": "admin"}


class CursorGuionado:
    """Responde segun un fragmento del SQL y guarda todo lo que se ejecuta."""

    def __init__(self, guion=()):
        self.guion = guion
        self.consultas = []
        self._uno = None
        self._todos = []
        self.cerrado = False

    def execute(self, sql, params=None):
        texto = " ".join(str(sql).split())
        self.consultas.append((texto, params))
        self._uno, self._todos = None, []
        for fragmento, uno, todos in self.guion:
            if fragmento in texto:
                self._uno, self._todos = uno, list(todos)
                break

    def fetchone(self):
        return self._uno

    def fetchall(self):
        return list(self._todos)

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


@pytest.fixture
def boletin(monkeypatch):
    """Instala un cursor guionado en el controlador del boletin."""

    def instalar(guion):
        cursor = CursorGuionado(guion)
        conexion = ConexionFalsa(cursor)
        monkeypatch.setattr(boletin_controller, "get_connection", lambda: conexion)
        return cursor, conexion

    return instalar


def _normalizar(sql):
    return " ".join(sql.split())


GUARDIA = ("SELECT al.anio, al.estado", (2026, "activo"), [])
RESUELVE = ("AS asignacion_academica_id", (55,), [])
NIVEL = ("SELECT c.nivel", (None,), [])


# --------------------------------------------------------------------------
# PB7: el SQL que calcula la nota de un periodo, letra por letra
# --------------------------------------------------------------------------

_PARTE_COMUN_ASIGNACIONES = """
    WITH asignaciones_academicas AS (
        SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
            COALESCE(a.asignacion_academica_id, a.id) AS id,
            a.curso_id, a.materia_id, a.profesor_id,
            COALESCE(a.orden_boletin, 100) AS orden_boletin
        FROM asignaciones a
        WHERE a.activo = TRUE
        ORDER BY COALESCE(a.asignacion_academica_id, a.id),
                 COALESCE(a.orden_boletin, 100), a.id
    )
"""

SQL_DE_HOY = {
    # Boletin del admin: la definitiva guardada o, si falta, el promedio en SQL.
    "materias_del_estudiante": (
        lambda c: boletin_repository.leer_materias_del_estudiante(
            c, 8, 2, NOMBRE_MATERIA_ASISTENCIA_JORNADA
        ),
        _PARTE_COMUN_ASIGNACIONES + """
        SELECT asig.id as asignacion_id, m.id as materia_id, m.nombre AS materia,
               p.nombre AS profesor_nombre, p.apellido AS profesor_apellido,
               COALESCE(NULLIF(bc.definitiva, 0), nd_prom.promedio_numerico) AS definitiva,
               bc.id as boletin_id, asig.orden_boletin
        FROM estudiantes e
        JOIN asignaciones_academicas asig ON e.curso_id = asig.curso_id
        JOIN materias m ON asig.materia_id = m.id
        JOIN profesor p ON asig.profesor_id = p.id
        LEFT JOIN boletin_cabecera bc ON bc.asignacion_id = asig.id
            AND bc.estudiante_id = e.id AND bc.periodo = %s
        LEFT JOIN LATERAL (
            SELECT AVG(nd.nota) AS promedio_numerico
            FROM notas_detalle nd
            WHERE nd.estudiante_id = e.id AND nd.asignacion_id = asig.id
              AND nd.periodo = %s
              AND COALESCE(nd.tipo_evaluacion, 'numerica') <> 'desarrollo'
              AND nd.nota > 0
        ) nd_prom ON TRUE
        WHERE e.id = %s AND m.nombre <> %s
          AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
        ORDER BY asig.orden_boletin, m.nombre
        """,
        (2, 2, 8, NOMBRE_MATERIA_ASISTENCIA_JORNADA),
    ),
    # Reporte parcial: las celdas del periodo; el promedio se saca en Python.
    "planilla_vigente": (
        lambda c: boletin_repository.leer_planilla_vigente(
            c, 8, 2, NOMBRE_MATERIA_ASISTENCIA_JORNADA
        ),
        _PARTE_COMUN_ASIGNACIONES + """
        SELECT asig.id AS asignacion_id, m.id AS materia_id, m.nombre AS materia,
               p.nombre AS profesor_nombre, p.apellido AS profesor_apellido,
               asig.orden_boletin, nd.id AS nota_detalle_id, nd.descripcion, nd.nota,
               COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
               nd.valoracion
        FROM estudiantes e
        JOIN asignaciones_academicas asig ON asig.curso_id = e.curso_id
        JOIN materias m ON m.id = asig.materia_id
        JOIN profesor p ON p.id = asig.profesor_id
        LEFT JOIN notas_detalle nd ON nd.estudiante_id = e.id
            AND nd.asignacion_id = asig.id AND nd.periodo = %s
        WHERE e.id = %s AND m.nombre <> %s
          AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
        ORDER BY asig.orden_boletin, m.nombre, nd.id
        """,
        (2, 8, NOMBRE_MATERIA_ASISTENCIA_JORNADA),
    ),
    # Boletin del profesor: las celdas con las que la pantalla saca la definitiva.
    "notas_de_planilla": (
        lambda c: boletin_repository.leer_notas_de_planilla(c, 55, 2),
        """
        SELECT e.id as estudiante_id, e.nombre, e.apellido,
               nd.descripcion as tipo_nota, nd.nota,
               COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
               nd.valoracion
        FROM estudiantes e
        JOIN asignaciones a ON e.curso_id = a.curso_id
        LEFT JOIN notas_detalle nd ON e.id = nd.estudiante_id
            AND nd.asignacion_id = a.id AND nd.periodo = %s
        WHERE a.id = %s AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
        ORDER BY e.apellido, e.nombre, nd.id
        """,
        (2, 55),
    ),
    # PB6: el puesto promedia las definitivas guardadas y no cambia su formula.
    # Desde 2026-11-23 el puesto no se repite: desempata por menos inasistencias
    # del periodo y luego por apellido y nombre (el promedio es el mismo).
    "puesto": (
        lambda c: boletin_repository.leer_puesto_en_el_curso(c, 8, 2),
        """
        WITH promedios AS (
            SELECT bc.estudiante_id, AVG(bc.definitiva) AS promedio
            FROM boletin_cabecera bc
            JOIN estudiantes e ON e.id = bc.estudiante_id
            JOIN asignaciones a ON a.id = bc.asignacion_id
            JOIN cursos c ON c.id = a.curso_id
            WHERE e.curso_id = (SELECT curso_id FROM estudiantes WHERE id = %s)
              AND c.anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
              AND bc.periodo = %s AND bc.definitiva IS NOT NULL
            GROUP BY bc.estudiante_id
        ), inasistencias AS (
            SELECT asi.estudiante_id, COUNT(*) AS ausencias
            FROM asistencia asi
            WHERE asi.estudiante_id IN (SELECT estudiante_id FROM promedios)
              AND asi.estado ILIKE 'ausente'
              AND COALESCE(asi.periodo, 1) = %s
              AND (asi.asignacion_id IS NULL OR asi.asignacion_id IN (
                  SELECT a.id FROM asignaciones a
                  JOIN cursos c ON c.id = a.curso_id
                  WHERE c.anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')
              ))
            GROUP BY asi.estudiante_id
        ), ranked AS (
            SELECT p.estudiante_id, p.promedio,
                   ROW_NUMBER() OVER (
                       ORDER BY p.promedio DESC,
                                COALESCE(i.ausencias, 0),
                                e.apellido, e.nombre, p.estudiante_id
                   ) AS puesto
            FROM promedios p
            JOIN estudiantes e ON e.id = p.estudiante_id
            LEFT JOIN inasistencias i ON i.estudiante_id = p.estudiante_id
        )
        SELECT (SELECT puesto FROM ranked WHERE estudiante_id = %s) AS puesto,
               (SELECT COUNT(*) FROM promedios) AS total
        """,
        (8, 2, 2, 8),
    ),
    # PB5: sin porcentajes activos se guarda la definitiva que llega.
    "cabecera": (
        lambda c: boletin_repository.guardar_cabecera(c, 8, 55, 2, 4.5),
        """
        INSERT INTO boletin_cabecera (estudiante_id, asignacion_id, periodo, definitiva)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (estudiante_id, asignacion_id, periodo)
        DO UPDATE SET definitiva = EXCLUDED.definitiva
        RETURNING id
        """,
        (8, 55, 2, 4.5),
    ),
    # Rankings de una clase y un periodo: promedio plano, truncado, con todas
    # las celdas (tambien `mas_alto`); las caritas no cuentan porque su nota es NULL.
    "ranking_bajo": (
        lambda c: dashboard_repository.leer_ranking_bajo_rendimiento(c, 77, 2),
        """
        SELECT e.id as estudiante_id, e.nombre || ' ' || e.apellido as nombre_estudiante,
               TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
        FROM notas_detalle n
        JOIN estudiantes e ON n.estudiante_id = e.id
        WHERE n.asignacion_id = %s AND n.periodo = %s
        GROUP BY e.id, e.nombre, e.apellido
        HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) < 3.0
        ORDER BY promedio ASC
        """,
        (77, 2),
    ),
    "ranking_mejor": (
        lambda c: dashboard_repository.leer_ranking_mejor_rendimiento(c, 77, 2),
        """
        SELECT e.id as estudiante_id, e.nombre || ' ' || e.apellido as nombre_estudiante,
               TRUNC(AVG(CAST(n.nota AS numeric)), 2) as promedio
        FROM notas_detalle n
        JOIN estudiantes e ON n.estudiante_id = e.id
        WHERE n.asignacion_id = %s AND n.periodo = %s
        GROUP BY e.id, e.nombre, e.apellido
        HAVING TRUNC(AVG(CAST(n.nota AS numeric)), 2) >= 3.0
        ORDER BY promedio DESC
        """,
        (77, 2),
    ),
}


@pytest.mark.parametrize("nombre", sorted(SQL_DE_HOY))
def test_el_sql_que_calcula_la_nota_del_periodo_no_cambia_ni_una_letra(nombre):
    llamar, sql_esperado, params_esperados = SQL_DE_HOY[nombre]
    cursor = CursorGuionado([("RETURNING id", (901,), [])])

    llamar(cursor)

    ((sql, params),) = cursor.consultas
    assert sql == _normalizar(sql_esperado)
    assert params == params_esperados


# --------------------------------------------------------------------------
# PB5: guardar el boletin sin porcentajes guarda la definitiva que llega
# --------------------------------------------------------------------------

class _Boletin:
    def __init__(self, definitiva, detalles):
        self.estudiante_id = 8
        self.asignacion_id = 44
        self.periodo = 2
        self.definitiva = definitiva
        self.tipo_evaluacion = "numerica"
        self.detalles = detalles


class _Detalle:
    def __init__(self, nota, observacion):
        self.nota = nota
        self.observacion = observacion
        self.tipo_evaluacion = "numerica"
        self.valoracion = None


@pytest.mark.parametrize(
    "definitiva",
    [4.5, 3.6666666666666665, 4.333333333333333, None],
    ids=["dos-decimales", "sin-redondear", "promedio-de-caritas", "sin-calificar"],
)
def test_guardar_boletin_guarda_la_definitiva_tal_como_llega(boletin, definitiva):
    cursor, conexion = boletin([
        GUARDIA, RESUELVE, NIVEL, ("INSERT INTO boletin_cabecera", (901,), []),
    ])
    datos = _Boletin(definitiva, [_Detalle(4.0, "Bien"), _Detalle(3.5, "Mejorar")])

    respuesta = boletin_controller.guardar_boletin_controller(datos, usuario=ADMIN)

    assert respuesta == {"mensaje": "Boletín guardado exitosamente"}
    escrituras = [
        (texto.split()[0], texto.split()[2], params)
        for texto, params in cursor.consultas
        if texto.split()[0] in ("INSERT", "DELETE", "UPDATE")
    ]
    assert escrituras == [
        ("INSERT", "boletin_cabecera", (8, 55, 2, definitiva)),
        ("DELETE", "boletin_detalles", (901,)),
        ("INSERT", "boletin_detalles", (901, 4.0, "Bien", "numerica", None)),
        ("INSERT", "boletin_detalles", (901, 3.5, "Mejorar", "numerica", None)),
    ]
    assert conexion.commits == 1
    assert conexion.rollbacks == 0


# --------------------------------------------------------------------------
# PB5: la lectura del boletin del profesor no trae definitiva
# --------------------------------------------------------------------------

def test_la_lectura_del_boletin_del_profesor_devuelve_el_json_de_hoy(boletin):
    celdas = [
        {"estudiante_id": 3, "nombre": "Sara", "apellido": "López", "tipo_nota": "Cognitivo",
         "nota": Decimal("4.50"), "tipo_evaluacion": "numerica", "valoracion": None},
        # Celda vacia: no llega a la pantalla.
        {"estudiante_id": 3, "nombre": "Sara", "apellido": "López", "tipo_nota": "Actitudinal",
         "nota": None, "tipo_evaluacion": "numerica", "valoracion": None},
        # El servidor si manda la columna interna; la pantalla la oculta.
        {"estudiante_id": 3, "nombre": "Sara", "apellido": "López", "tipo_nota": "mas_alto",
         "nota": Decimal("5.00"), "tipo_evaluacion": "numerica", "valoracion": None},
        {"estudiante_id": 4, "nombre": "Eva", "apellido": "Ríos", "tipo_nota": "Cognitivo",
         "nota": None, "tipo_evaluacion": "desarrollo", "valoracion": "logrado"},
        {"estudiante_id": 5, "nombre": "Leo", "apellido": "Soto", "tipo_nota": None,
         "nota": None, "tipo_evaluacion": "numerica", "valoracion": None},
    ]
    guardado = [
        {"estudiante_id": 3, "definitiva": Decimal("4.75"), "nota": Decimal("4.50"),
         "observacion": "Muy bien", "tipo_evaluacion": "numerica", "valoracion": None},
    ]
    boletin([
        RESUELVE,
        ("nd.descripcion as tipo_nota", None, celdas),
        ("bc.estudiante_id = ANY(%s)", None, guardado),
    ])

    respuesta = boletin_controller.obtener_boletin_para_profesor_controller(44, 2)

    assert respuesta == [
        {
            "estudiante_id": 3,
            "nombre": "Sara López",
            "notas": [
                {"tipo_nota": "Cognitivo", "valor": 4.5, "tipo_evaluacion": "numerica",
                 "valoracion": None, "observacion_guardada": "Muy bien"},
                {"tipo_nota": "mas_alto", "valor": 5.0, "tipo_evaluacion": "numerica",
                 "valoracion": None, "observacion_guardada": ""},
            ],
            # 2026-11-23: lo guardado, para avisar si la planilla cambio despues.
            "guardado": {"definitiva": 4.75, "detalles": [{"valor": 4.5, "valoracion": None}]},
        },
        {
            "estudiante_id": 4,
            "nombre": "Eva Ríos",
            "notas": [
                {"tipo_nota": "Cognitivo", "valor": None, "tipo_evaluacion": "desarrollo",
                 "valoracion": "logrado", "observacion_guardada": ""},
            ],
            "guardado": None,
        },
        {"estudiante_id": 5, "nombre": "Leo Soto", "notas": [], "guardado": None},
    ]


def test_la_lectura_del_boletin_del_profesor_trae_las_caritas_guardadas_en_su_orden(boletin):
    """2026-11-23: con esto la pantalla ve que el boletin guardado tiene 😀
    donde la planilla ya dice ⭐ (lo que paso en Jardin A, periodo 4)."""
    celdas = [
        {"estudiante_id": 8, "nombre": "Moises", "apellido": "Lopez", "tipo_nota": tipo,
         "nota": None, "tipo_evaluacion": "desarrollo", "valoracion": "destacado"}
        for tipo in ("Del 1al9", "Fam 10")
    ]
    guardado = [
        {"estudiante_id": 8, "definitiva": Decimal("4.50"), "nota": None,
         "observacion": texto, "tipo_evaluacion": "desarrollo", "valoracion": valoracion}
        for texto, valoracion in (("Numeros del 1 al 9", "destacado"), ("Familia del 10", "logrado"))
    ]
    boletin([
        RESUELVE,
        ("nd.descripcion as tipo_nota", None, celdas),
        ("bc.estudiante_id = ANY(%s)", None, guardado),
    ])

    (moises,) = boletin_controller.obtener_boletin_para_profesor_controller(44, 4)

    assert moises["guardado"] == {
        "definitiva": 4.5,
        "detalles": [
            {"valor": None, "valoracion": "destacado"},
            {"valor": None, "valoracion": "logrado"},
        ],
    }
    # Lo de siempre no cambia: la planilla manda la carita de hoy y el texto guardado.
    assert [(n["valoracion"], n["observacion_guardada"]) for n in moises["notas"]] == [
        ("destacado", "Numeros del 1 al 9"),
        ("destacado", "Familia del 10"),
    ]


# --------------------------------------------------------------------------
# PB7: el boletin del admin y el reporte parcial, con sus diferencias de hoy
# --------------------------------------------------------------------------

def _materia(asignacion_id, materia, definitiva):
    return {
        "asignacion_id": asignacion_id, "materia_id": asignacion_id + 100, "materia": materia,
        "profesor_nombre": "Ana", "profesor_apellido": "Ruiz",
        "definitiva": definitiva, "boletin_id": None, "orden_boletin": 1,
    }


def test_el_boletin_del_admin_entrega_la_definitiva_de_sql_sin_redondear(boletin):
    boletin([
        ("AS promedio_numerico", None, [
            _materia(44, "Historia", Decimal("3.6666666666666667")),
            _materia(45, "Arte", None),
        ]),
        ("as director_grupo_nombre", {
            "estudiante_nombre": "Sara", "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        }, []),
        ("AS puesto", {"puesto": 2, "total": 30}, []),
    ])

    respuesta = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert [m["definitiva"] for m in respuesta["materias"]] == [3.6666666666666665, None]
    assert (respuesta["puesto"], respuesta["total_estudiantes"]) == (2, 30)


def _celda(asignacion_id, materia, celda_id, descripcion, nota, tipo="numerica",
           valoracion=None):
    return {
        "asignacion_id": asignacion_id, "materia_id": asignacion_id + 100, "materia": materia,
        "profesor_nombre": "Ana", "profesor_apellido": "Ruiz", "orden_boletin": 1,
        "nota_detalle_id": celda_id, "descripcion": descripcion, "nota": nota,
        "tipo_evaluacion": tipo, "valoracion": valoracion,
    }


def test_el_reporte_parcial_cuenta_la_columna_interna_y_deja_vacia_la_materia_sin_notas(
    boletin,
):
    """QB4: la diferencia se conserva. La planilla y el boletin del profesor
    ocultan `mas_alto` en la pantalla; el reporte parcial la promedia."""
    boletin([
        ("AS director_grupo_nombre", {
            "estudiante_nombre": "Sara", "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        }, []),
        ("AS nota_detalle_id", None, [
            _celda(44, "Historia", 101, "Cognitivo", Decimal("3.00")),
            _celda(44, "Historia", 102, "mas_alto", Decimal("5.00")),
            _celda(44, "Historia", 103, "Actitudinal", None),
            _celda(45, "Arte", None, None, None),
        ]),
    ])

    respuesta = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    historia, arte = respuesta["materias"]
    assert historia["definitiva"] == 4.0
    assert [d["descripcion"] for d in historia["detalles"]] == [
        "Cognitivo", "mas_alto", "Actitudinal",
    ]
    assert arte["definitiva"] is None
    assert arte["detalles"] == []


# --------------------------------------------------------------------------
# PB7: el promedio que calcula el servidor para la planilla
# --------------------------------------------------------------------------

def test_el_promedio_de_la_planilla_redondea_como_python_y_cuenta_mas_alto(monkeypatch):
    """`round` de Python redondea al par: 3.625 queda en 3.62 y 4.125 en 4.12.
    Con porcentajes activos (PB4) seria mitad hacia arriba, 3.63 y 4.13; sin
    ellos tiene que seguir dando esto (QB4). La pantalla no usa este promedio:
    lo recalcula en `utils/planilla/notas.js`."""
    filas = [
        # (estudiante, nombre, apellido, materia, descripcion, nota, tipo, valoracion, id)
        (1, "Ana", "Gómez", "Lengua", "Cognitivo", Decimal("3.25"), "numerica", None, 10),
        (1, "Ana", "Gómez", "Lengua", "Procedimental", Decimal("4.00"), "numerica", None, 11),
        (2, "Luis", "Pérez", "Lengua", "Cognitivo", Decimal("4.00"), "numerica", None, 12),
        (2, "Luis", "Pérez", "Lengua", "Procedimental", Decimal("4.25"), "numerica", None, 13),
        (3, "Eva", "Ríos", "Lengua", "Cognitivo", Decimal("3.00"), "numerica", None, 14),
        (3, "Eva", "Ríos", "Lengua", "mas_alto", Decimal("5.00"), "numerica", None, 15),
    ]
    cursor = CursorGuionado([
        ("AS asignacion_academica_id", (77,), []),
        ("FROM asignaciones a JOIN cursos c", None, filas),
    ])

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(planilla_excel_controller, "get_cursor", fake_get_cursor)

    respuesta = planilla_excel_controller.planilla_excel_controller(12, 2)

    promedios = {est["nombre"]: est["promedio"] for est in respuesta["data"]}
    assert promedios == {"Ana": 3.62, "Luis": 4.12, "Eva": 4.0}
    assert respuesta["columnas"] == ["Cognitivo", "Procedimental", "mas_alto"]
