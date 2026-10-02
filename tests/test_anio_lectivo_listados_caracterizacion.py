"""Caracterizacion de listados antes de la funcionalidad "Año lectivo".

Fase 0 de `docs/funcionalidades/ANIO_LECTIVO.md`. La fase 3 agrega un filtro
por año a estos listados, con el año activo por defecto, y promete que **sin
el parametro la respuesta es identica a la de hoy**. Estas pruebas fijan la
respuesta completa (campos, valores por defecto, orden de los parametros)
para que esa promesa se pueda comprobar.

Solo cubre lo que no estaba fijado ya:

- Cursos: `test_curso_controlador.py` revisa campos sueltos (nivel,
  director); aqui se fija la respuesta entera y sus parametros.
- Conceptos de pago: sus tres listados no tenian ninguna prueba.

Ya estaban fijados con la respuesta completa, y sirven igual para la fase 3:
estudiantes (`test_asignaciones_estudiantes_caracterizacion.py`), "mis
clases" del profesor (`test_asignaciones_pagination.py`), boletin
(`test_boletin_caracterizacion.py`) y listas de seguimiento
(`test_listas_seguimiento_repositorio.py`).

Son dobles de cursor, sin base de datos: fijan el contrato de la respuesta y
de los parametros, no que el SQL filtre bien. Eso ultimo se comprueba en la
fase 3 contra una rama de Neon.
"""
from decimal import Decimal

import pytest

from app.controllers import curso_controller, tipos_pagos_controller
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL


class CursorEspia:
    """Registra cada execute y sirve las respuestas en el orden pedido."""

    def __init__(self, una=None, todas=None):
        self.ejecutadas = []
        self._una = list(una or [])
        self._todas = list(todas or [])

    def execute(self, query, params=None):
        self.ejecutadas.append((query, params))

    def fetchone(self):
        return self._una.pop(0) if self._una else None

    def fetchall(self):
        return self._todas.pop(0) if self._todas else []

    def close(self):
        pass

    @property
    def sql(self):
        return [query for query, _ in self.ejecutadas]

    @property
    def parametros(self):
        return [params for _, params in self.ejecutadas]


class ConexionEspia:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.commits += 1

    def close(self):
        pass


@pytest.fixture
def conexion_de(monkeypatch):
    def instalar(modulo, **kwargs):
        cursor = CursorEspia(**kwargs)
        conn = ConexionEspia(cursor)
        monkeypatch.setattr(modulo, "get_connection", lambda: conn)
        return cursor, conn

    return instalar


# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------


def test_cursos_listado_completo_filtra_activos_por_defecto(conexion_de):
    cursor, conn = conexion_de(
        curso_controller,
        todas=[[
            (1, "TRANSICIÓN A", "Mañana", "activo", "preescolar", 7),
            (2, "PRIMERO A", None, "activo", None, None),
        ]],
    )

    respuesta = curso_controller.obtener_cursos_controller()

    assert respuesta == [
        {
            "id": 1,
            "nombre": "TRANSICIÓN A",
            "jornada": "Mañana",
            "estado": "activo",
            "nivel": "preescolar",
            "director_grupo_id": 7,
        },
        {
            "id": 2,
            "nombre": "PRIMERO A",
            "jornada": "Mañana",
            "estado": "activo",
            "nivel": None,
            "director_grupo_id": None,
        },
    ]
    assert len(cursor.ejecutadas) == 1
    assert "FROM cursos" in cursor.sql[0]
    assert "COALESCE(LOWER(estado), 'activo') = %s" in cursor.sql[0]
    assert "ORDER BY id" in cursor.sql[0]
    assert cursor.parametros[0] == ["activo"]
    assert conn.commits == 0


def test_cursos_listado_con_todos_no_filtra(conexion_de):
    cursor, _ = conexion_de(curso_controller, todas=[[]])

    respuesta = curso_controller.obtener_cursos_controller(estado="todos")

    assert respuesta == []
    # Fase 3, paso 3.3: "todos" sigue sin filtrar por estado, pero ahora
    # si filtra por año (el activo, sin parametro). Antes se pedia que no
    # hubiera ningun WHERE; lo que importa es que no se filtre el estado.
    assert "COALESCE(LOWER(estado), 'activo') = %s" not in cursor.sql[0]
    assert f"WHERE anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}" in cursor.sql[0]
    assert cursor.parametros[0] == []


def test_cursos_paginado_respuesta_completa_y_orden_de_parametros(conexion_de):
    cursor, _ = conexion_de(
        curso_controller,
        una=[(13,)],
        todas=[[(2, "PRIMERO A", "Tarde", "activo", "primaria", None)]],
    )

    respuesta = curso_controller.obtener_cursos_paginado_controller(
        limit=10, offset=20, busqueda="pri",
    )

    assert respuesta == {
        "total": 13,
        "limit": 10,
        "offset": 20,
        "items": [
            {
                "id": 2,
                "nombre": "PRIMERO A",
                "jornada": "Tarde",
                "estado": "activo",
                "nivel": "primaria",
                "director_grupo_id": None,
            },
        ],
    }
    assert len(cursor.ejecutadas) == 2
    assert "SELECT COUNT(*) FROM cursos" in cursor.sql[0]
    assert cursor.parametros[0] == ["%pri%", "activo"]
    assert cursor.parametros[1] == ["%pri%", "activo", 10, 20]


# ---------------------------------------------------------------------------
# Conceptos de pago
# ---------------------------------------------------------------------------


def test_conceptos_listado_simple_respuesta_completa(conexion_de):
    cursor, _ = conexion_de(
        tipos_pagos_controller,
        todas=[[
            (2, "MATRICULA", Decimal("300000.00")),
            (1, "MENSUALIDAD", None),
        ]],
    )

    respuesta = tipos_pagos_controller.listar_tipos_pagos()

    assert respuesta == [
        {"id": 2, "nombre": "MATRICULA", "valor": 300000.0},
        {"id": 1, "nombre": "MENSUALIDAD", "valor": 0},
    ]
    # Fase 3, paso 3.3: solo los conceptos del año activo, sin parametro nuevo.
    assert cursor.sql == [
        "SELECT id, nombre, valor FROM tipos_de_pagos"
        f" WHERE anio_lectivo_id = {ANIO_ACTIVO_ID_SQL} ORDER BY nombre"
    ]
    assert cursor.parametros == [None]


def _concepto_fila(**valores):
    """Fila de `SELECT * FROM tipos_de_pagos` como la entrega RealDictCursor."""
    fila = {
        "id": 1,
        "nombre": "MENSUALIDAD",
        "valor": Decimal("0.00"),
        "descripcion": None,
        "tipo_cobro": "mensual",
        "fecha_limite": None,
        "dia_limite_mes": 5,
        "dias_gracia": 0,
        "mora_tipo": None,
        "mora_valor": Decimal("0.00"),
        "mes_inicial": 7,
        "mes_final": 11,
        "frecuencia_meses": 1,
        "generacion_automatica": False,
        "activo": True,
    }
    fila.update(valores)
    return fila


def test_conceptos_detallado_respuesta_completa_con_cursos(conexion_de):
    columnas = [{"column_name": nombre} for nombre in _concepto_fila()]
    tablas = [{"table_name": "tipos_de_pagos"}, {"table_name": "tipos_pagos_cursos"}]
    cursor, _ = conexion_de(
        tipos_pagos_controller,
        todas=[
            columnas,
            [
                _concepto_fila(
                    id=2, nombre="MATRICULA", valor=Decimal("300000.00"),
                    tipo_cobro="anual", dia_limite_mes=None, mes_inicial=2,
                    mes_final=12, activo=False,
                ),
                _concepto_fila(),
            ],
            tablas,
            [
                {"tipo_pago_id": 1, "curso_id": 4, "valor": Decimal("180000.00"),
                 "activo": True, "curso_nombre": "PRIMERO A"},
                {"tipo_pago_id": 1, "curso_id": 9, "valor": None,
                 "activo": False, "curso_nombre": "TRANSICIÓN A"},
            ],
        ],
    )

    respuesta = tipos_pagos_controller.listar_tipos_pagos_detallado()

    configuracion_comun = {
        "descripcion": None,
        "fecha_limite": None,
        "dias_gracia": 0,
        "mora_tipo": None,
        "mora_valor": 0.0,
        "frecuencia_meses": 1,
        "generacion_automatica": False,
    }
    assert respuesta == [
        {
            "id": 2,
            "nombre": "MATRICULA",
            "valor": 300000.0,
            **configuracion_comun,
            "tipo_cobro": "anual",
            "dia_limite_mes": None,
            "mes_inicial": 2,
            "mes_final": 12,
            "activo": False,
            "cursos": [],
        },
        {
            "id": 1,
            "nombre": "MENSUALIDAD",
            "valor": 0.0,
            **configuracion_comun,
            "tipo_cobro": "mensual",
            "dia_limite_mes": 5,
            "mes_inicial": 7,
            "mes_final": 11,
            "activo": True,
            "cursos": [
                {"curso_id": 4, "curso_nombre": "PRIMERO A", "valor": 180000.0, "activo": True},
                {"curso_id": 9, "curso_nombre": "TRANSICIÓN A", "valor": 0, "activo": False},
            ],
        },
    ]
    assert len(cursor.ejecutadas) == 4
    # Fase 3, paso 3.3: solo los conceptos del año activo, sin parametro nuevo.
    assert (
        f"SELECT * FROM tipos_de_pagos WHERE anio_lectivo_id = {ANIO_ACTIVO_ID_SQL} ORDER BY nombre"
        in cursor.sql[1]
    )
    assert cursor.parametros[1] is None
    assert "FROM tipos_pagos_cursos tpc" in cursor.sql[3]
    assert "ORDER BY c.nombre" in cursor.sql[3]


def test_cursos_de_un_concepto_respuesta_completa(conexion_de):
    cursor, _ = conexion_de(
        tipos_pagos_controller,
        todas=[
            [{"table_name": "tipos_pagos_cursos"}],
            [
                {"id": 31, "tipo_pago_id": 1, "curso_id": 4, "valor": Decimal("180000.00"),
                 "activo": True, "curso_nombre": "PRIMERO A"},
            ],
        ],
    )

    respuesta = tipos_pagos_controller.listar_cursos_asignados(1)

    assert respuesta == [
        {
            "id": 31,
            "tipo_pago_id": 1,
            "curso_id": 4,
            "curso_nombre": "PRIMERO A",
            "valor": 180000.0,
            "activo": True,
        },
    ]
    assert len(cursor.ejecutadas) == 2
    assert "WHERE tpc.tipo_pago_id = %s" in cursor.sql[1]
    assert cursor.parametros[1] == (1,)
