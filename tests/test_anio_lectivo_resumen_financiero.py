"""Fase 5.6: resumen y recorrido financiero del año en preparación.

Todo usa dobles o cálculo puro. No se crea 2027 en una base real, no se
registran pagos reales y no se ejecutan migraciones.
"""
from contextlib import contextmanager
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.controllers import anios_lectivos_controller as controlador_anios
from app.controllers import pagos_controller, tipos_pagos_controller
from app.repositories import anios_lectivos_repository as repositorio_anios
from app.routes import anios_lectivos as rutas_anios
from app.routes import tipos_pagos as rutas_tipos_pagos
from app.schemas.pago import PagoCreate
from app.services import cobros


class CursorFalso:
    def __init__(self, una=(), todas=()):
        self.una = list(una)
        self.todas = list(todas)
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(str(sql).split()), params))

    def fetchone(self):
        return self.una.pop(0) if self.una else None

    def fetchall(self):
        return self.todas.pop(0) if self.todas else []

    def close(self):
        pass


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False

    def cursor(self, cursor_factory=None):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


def test_el_resumen_reune_la_preparacion_y_sus_pagos(monkeypatch):
    cursor = object()
    resumen = {
        "id": 3,
        "anio": 2027,
        "estado": "preparacion",
        "cursos": 12,
        "conceptos_pago": 2,
        "estudiantes_matriculados": 174,
        "valores_especiales": 5,
        "pagos_registrados": 1,
        "total_pagado": 250000,
    }

    @contextmanager
    def cursor_falso(commit=False):
        assert commit is False
        yield cursor

    monkeypatch.setattr(controlador_anios, "get_cursor", cursor_falso)
    monkeypatch.setattr(
        controlador_anios,
        "_contexto_matricula_en_preparacion",
        lambda cursor_recibido, anio_id: (
            (2, 2026, "activo"),
            (anio_id, 2027, "preparacion"),
        ),
    )
    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "leer_resumen_anio",
        lambda cursor_recibido, anio_id: resumen,
        raising=False,
    )

    funcion = getattr(controlador_anios, "resumen_anio_preparacion_controller")
    respuesta = funcion(3)

    assert respuesta == {
        "anio_lectivo": {"id": 3, "anio": 2027, "estado": "preparacion"},
        "resumen": {
            "cursos": 12,
            "conceptos_pago": 2,
            "estudiantes_matriculados": 174,
            "valores_especiales": 5,
            "pagos_registrados": 1,
            "total_pagado": 250000.0,
        },
    }


def test_el_sql_del_resumen_cuenta_solo_el_anio_y_excluye_pagos_anulados():
    cursor = CursorFalso(
        una=[(3, 2027, "preparacion", 12, 2, 174, 5, 1, 250000)]
    )

    resultado = getattr(repositorio_anios, "leer_resumen_anio")(cursor, 3)

    sql, params = cursor.consultas[0]
    assert "WITH seleccionado AS" in sql
    assert "FROM cursos c" in sql
    assert "FROM tipos_de_pagos tp" in sql
    assert "FROM matriculas m" in sql
    assert "FROM tipos_pagos_estudiantes tpe" in sql
    assert "FROM pagos p" in sql
    assert "COALESCE(LOWER(p.estado), 'pagado') <> 'anulado'" in sql
    assert params == (3,)
    assert resultado["total_pagado"] == 250000


def test_la_ruta_de_resumen_es_solo_admin_y_traduce_errores(monkeypatch):
    from app.dependencies import get_current_active_admin

    ruta = next(
        ruta
        for ruta in rutas_anios.router.routes
        if ruta.path == "/anios-lectivos/{anio_lectivo_id}/resumen"
    )
    assert get_current_active_admin in [
        dependencia.call for dependencia in ruta.dependant.dependencies
    ]

    def rechazar(_anio_id):
        raise controlador_anios.AnioLectivoDestinoInvalidoError(
            "El año no está en preparación."
        )

    monkeypatch.setattr(
        rutas_anios, "resumen_anio_preparacion_controller", rechazar
    )
    with pytest.raises(HTTPException) as error:
        rutas_anios.resumen_anio_preparacion(3)
    assert error.value.status_code == 409


def _fila_valor():
    return {
        "id": 91,
        "tipo_pago_id": 40,
        "estudiante_id": 7,
        "valor": 250000,
        "motivo": "Beca parcial",
        "activo": True,
        "created_at": datetime(2026, 10, 6, 8, 0),
        "updated_at": datetime(2026, 10, 6, 8, 0),
        "tipo_pago_nombre": "MATRICULA",
        "valor_base": 300000,
        "valor_curso": 300000,
    }


@pytest.mark.parametrize(
    ("anio_lectivo_id", "fragmento", "params"),
    [
        (None, "t.anio_lectivo_id = (SELECT id FROM anios_lectivos", (7,)),
        (3, "t.anio_lectivo_id = %s", (7, 3)),
    ],
)
def test_los_valores_se_leen_con_el_curso_de_la_matricula_del_mismo_anio(
    monkeypatch, anio_lectivo_id, fragmento, params
):
    cursor = CursorFalso(todas=[[_fila_valor()]])
    monkeypatch.setattr(
        tipos_pagos_controller,
        "_exigir_tabla_valores_estudiantes",
        lambda _cursor: None,
    )

    valores = tipos_pagos_controller._consultar_valores_personalizados(
        cursor, 7, anio_lectivo_id=anio_lectivo_id
    )

    sql, recibidos = cursor.consultas[0]
    assert "JOIN matriculas m" in sql
    assert "m.anio_lectivo_id = t.anio_lectivo_id" in sql
    assert "tpc.curso_id = m.curso_id" in sql
    assert "e.curso_id" not in sql
    assert fragmento in sql
    assert recibidos == params
    assert valores == [
        {
            "id": 91,
            "tipo_pago_id": 40,
            "estudiante_id": 7,
            "tipo_pago_nombre": "MATRICULA",
            "valor": 250000.0,
            "valor_base": 300000.0,
            "valor_curso": 300000.0,
            "motivo": "Beca parcial",
            "activo": True,
            "created_at": "2026-10-06T08:00:00",
            "updated_at": "2026-10-06T08:00:00",
        }
    ]


def test_la_lectura_publica_valida_y_pasa_el_anio(monkeypatch):
    cursor = CursorFalso()
    conexion = ConexionFalsa(cursor)
    eventos = []

    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(
        tipos_pagos_controller,
        "exigir_anio_lectivo",
        lambda cursor_recibido, anio_id: eventos.append(("anio", anio_id)),
    )
    monkeypatch.setattr(
        tipos_pagos_controller,
        "_consultar_valores_personalizados",
        lambda cursor_recibido, estudiante_id, anio_lectivo_id=None: eventos.append(
            ("consulta", estudiante_id, anio_lectivo_id)
        ) or [],
    )

    tipos_pagos_controller.listar_valores_personalizados_estudiante(
        7, anio_lectivo_id=3
    )
    tipos_pagos_controller.listar_valores_personalizados_estudiante(7)

    assert eventos == [
        ("anio", 3),
        ("consulta", 7, 3),
        ("consulta", 7, None),
    ]


def test_la_ruta_de_valores_acepta_el_anio_opcional_y_lo_pasa(monkeypatch):
    ruta = next(
        ruta
        for ruta in rutas_tipos_pagos.router.routes
        if isinstance(ruta, APIRoute)
        and ruta.path == "/estudiantes/{estudiante_id}/valores-pago-personalizados"
    )
    parametros = {parametro.name: parametro for parametro in ruta.dependant.query_params}
    assert set(parametros) == {"anio_lectivo_id"}
    assert parametros["anio_lectivo_id"].field_info.default is None

    recibidos = []
    monkeypatch.setattr(
        rutas_tipos_pagos,
        "listar_valores_personalizados_estudiante",
        lambda estudiante_id, **kwargs: recibidos.append((estudiante_id, kwargs)) or [],
    )

    rutas_tipos_pagos.get_valores_personalizados_estudiante(7, anio_lectivo_id=3)
    rutas_tipos_pagos.get_valores_personalizados_estudiante(7)
    assert recibidos == [
        (7, {"anio_lectivo_id": 3}),
        (7, {"anio_lectivo_id": None}),
    ]


class CursorValor:
    def __init__(self, curso_id=20, estudiante_id=7):
        self.curso_id = curso_id
        self.estudiante_id = estudiante_id
        self.consultas = []
        self.actual = []

    def execute(self, sql, params=None):
        normalizada = " ".join(str(sql).split())
        self.consultas.append((normalizada, params))
        if "SELECT tp.anio_lectivo_id, m.curso_id" in normalizada:
            self.actual = [(3, self.curso_id, self.estudiante_id)]
        elif "SELECT 1 FROM tipos_pagos_cursos" in normalizada:
            self.actual = [(1,)]
        elif "INSERT INTO tipos_pagos_estudiantes" in normalizada:
            self.actual = [(91,)]
        else:
            self.actual = []

    def fetchone(self):
        return self.actual[0] if self.actual else None

    def fetchall(self):
        return list(self.actual)

    def close(self):
        pass


def _preparar_upsert(monkeypatch, curso_id=20, estudiante_id=7):
    cursor = CursorValor(curso_id=curso_id, estudiante_id=estudiante_id)
    conexion = ConexionFalsa(cursor)
    releido = []
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(
        tipos_pagos_controller,
        "exigir_concepto_editable_para_admin",
        lambda _cursor, _tipo_pago_id: None,
    )
    monkeypatch.setattr(
        tipos_pagos_controller,
        "_exigir_tabla_valores_estudiantes",
        lambda _cursor: None,
    )
    monkeypatch.setattr(
        tipos_pagos_controller,
        "_table_names",
        lambda _cursor: {"tipos_pagos_cursos", "tipos_pagos_estudiantes"},
    )
    monkeypatch.setattr(
        tipos_pagos_controller,
        "_consultar_valores_personalizados",
        lambda _cursor, estudiante_id, anio_lectivo_id=None: releido.append(
            (estudiante_id, anio_lectivo_id)
        ) or [],
    )
    return conexion, cursor, releido


def test_guardar_un_valor_usa_la_matricula_del_anio_del_concepto(monkeypatch):
    conexion, cursor, releido = _preparar_upsert(monkeypatch)

    tipos_pagos_controller.upsert_valor_personalizado_estudiante(7, 40, 250000)

    consulta_contexto = next(
        consulta for consulta in cursor.consultas
        if "SELECT tp.anio_lectivo_id, m.curso_id" in consulta[0]
    )
    assert "FROM tipos_de_pagos tp" in consulta_contexto[0]
    assert "LEFT JOIN matriculas m" in consulta_contexto[0]
    assert consulta_contexto[1] == (7, 40)
    consulta_asignacion = next(
        consulta for consulta in cursor.consultas
        if "SELECT 1 FROM tipos_pagos_cursos" in consulta[0]
    )
    assert consulta_asignacion[1] == (40, 20)
    assert releido == [(7, 3)]
    assert conexion.commits == 1


def test_guardar_un_valor_rechaza_al_estudiante_sin_matricula_en_ese_anio(
    monkeypatch,
):
    conexion, cursor, _releido = _preparar_upsert(monkeypatch, curso_id=None)

    with pytest.raises(ValueError, match="no tiene matrícula"):
        tipos_pagos_controller.upsert_valor_personalizado_estudiante(
            7, 40, 250000
        )

    assert not any(
        "INSERT INTO tipos_pagos_estudiantes" in consulta
        for consulta, _params in cursor.consultas
    )
    assert conexion.rollbacks == 1


def test_guardar_un_valor_conserva_el_error_de_estudiante_inexistente(monkeypatch):
    conexion, cursor, _releido = _preparar_upsert(
        monkeypatch, curso_id=None, estudiante_id=None
    )

    with pytest.raises(ValueError, match="Estudiante no encontrado"):
        tipos_pagos_controller.upsert_valor_personalizado_estudiante(
            7, 40, 250000
        )

    assert not any(
        "INSERT INTO tipos_pagos_estudiantes" in consulta
        for consulta, _params in cursor.consultas
    )
    assert conexion.rollbacks == 1


def _concepto_matricula(concepto_id, anio):
    return {
        "id": concepto_id,
        "nombre": "MATRICULA",
        "valor": 300000,
        "tipo_cobro": "anual",
        "activo": True,
        "anio": anio,
        "mes_inicial": None,
        "mes_final": 12,
        "frecuencia_meses": 1,
        "dia_limite_mes": None,
        "dias_gracia": 0,
        "mora_tipo": None,
        "mora_valor": 0,
    }


def test_recorrido_matricula_2027_pagada_en_noviembre_de_2026(monkeypatch):
    """Valor copiado -> deuda 2027 -> pago anticipado -> deuda 2027 en cero."""
    estado = {"valores_2027": {}, "pagos": []}
    valor_origen = {
        "id": 71,
        "tipo_pago_origen_id": 30,
        "tipo_pago_origen_nombre": "MATRICULA",
        "tipo_pago_destino_id": 40,
        "tipo_pago_destino_nombre": "MATRICULA",
        "valor": 250000,
        "motivo": "Beca parcial",
        "activo": True,
    }

    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "listar_valores_especiales_para_copiar",
        lambda _cursor, estudiante_id, origen_id, destino_id: [valor_origen],
    )

    def insertar_valor(_cursor, estudiante_id, valor):
        estado["valores_2027"][valor["tipo_pago_destino_id"]] = valor["valor"]
        return 91

    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "insertar_valor_especial_copiado",
        insertar_valor,
    )
    copiados = controlador_anios._copiar_valores_especiales(
        object(), 7, 2, 3
    )
    assert copiados[0]["estado"] == "revisar"

    def deuda_2027():
        pagado = sum(
            pago["monto"] for pago in estado["pagos"]
            if pago["anio_lectivo_id"] == 3
        )
        return cobros._calcular_deudas(
            tipos_pago=[_concepto_matricula(40, 2027)],
            asignaciones_curso={40: 300000},
            valores_estudiante=estado["valores_2027"],
            pagos_nombre={"matricula": pagado},
            pagos_descripcion={},
            hoy=date(2026, 11, 15),
        )

    antes = deuda_2027()
    assert antes["total_deuda"] == 250000
    assert antes["deudas"][0]["valor_personalizado"] is True

    cursor_pago = CursorFalso()
    conexion = ConexionFalsa(cursor_pago)
    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(
        pagos_controller, "_bloquear_registro_de_pagos", lambda *_args: None
    )
    monkeypatch.setattr(
        pagos_controller,
        "exigir_anio_lectivo",
        lambda _cursor, anio_id: (anio_id, 2027, "preparacion"),
    )
    monkeypatch.setattr(
        pagos_controller,
        "obtener_saldo_concepto",
        lambda _cursor, _estudiante, _concepto, anio_lectivo_id=None: (
            deuda_2027()["total_deuda"] if anio_lectivo_id == 3 else 0
        ),
    )

    def insertar_pago(
        _cursor,
        estudiante_id,
        venta_id,
        monto,
        descripcion,
        fecha,
        tipo_pago,
        anio_lectivo_id=None,
    ):
        estado["pagos"].append(
            {
                "estudiante_id": estudiante_id,
                "monto": monto,
                "descripcion": descripcion,
                "fecha": fecha,
                "tipo_pago": tipo_pago,
                "anio_lectivo_id": anio_lectivo_id,
            }
        )
        return 501

    monkeypatch.setattr(pagos_controller, "insertar_pago", insertar_pago)

    pago_id = pagos_controller.registrar_pago_controller(
        PagoCreate(
            estudiante_id=7,
            monto=250000,
            descripcion="MATRICULA",
            fecha=date(2026, 11, 15),
            metodos=[{"tipo": "Transferencia", "monto": 250000}],
            anio_lectivo_id=3,
        )
    )

    assert pago_id == 501
    pago_registrado = estado["pagos"][0]
    assert {
        **pago_registrado,
        "fecha": pago_registrado["fecha"].date(),
    } == {
        "estudiante_id": 7,
        "monto": 250000.0,
        "descripcion": "MATRICULA",
        "fecha": date(2026, 11, 15),
        "tipo_pago": "Transferencia",
        "anio_lectivo_id": 3,
    }
    assert deuda_2027()["total_deuda"] == 0
    assert conexion.commits == 1

    deuda_2026 = cobros._calcular_deudas(
        tipos_pago=[_concepto_matricula(30, 2026)],
        asignaciones_curso={30: 300000},
        valores_estudiante={},
        pagos_nombre={"matricula": 300000},
        pagos_descripcion={},
        hoy=date(2026, 11, 15),
    )
    assert deuda_2026["total_deuda"] == 0
