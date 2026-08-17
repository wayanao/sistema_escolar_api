"""Caracterizacion de la subcapa 5.0: dominio de pagos y tipos de pago.

Esta es la primera capa del programa que **escribe**. Un error aqui no produce un
informe equivocado sino datos financieros equivocados, asi que la linea base fija
tres cosas que una extraccion posterior podria romper en silencio:

1. la frontera HTTP completa, con metodo, permiso admin, ejecucion sincrona y
   presencia de body;
2. el contrato transaccional de cada escritura: cuantas sentencias emite, quien
   confirma, quien revierte y quien cierra conexion y cursor;
3. las columnas que la capa 4 lee, que se escriben aqui.

No prueba comportamiento nuevo ni corrige nada: congela lo que hoy ocurre,
incluidas las rarezas.
"""

import inspect
from datetime import date, datetime

import pytest
from fastapi.routing import APIRoute
from psycopg2 import IntegrityError

from app.controllers import pagos_controller, tipos_pagos_controller
from app.dependencies import get_current_active_admin
from app.routes import pagos as rutas_pagos
from app.routes import tipos_pagos as rutas_tipos_pagos
from app.schemas.pago import (
    MetodoPago,
    PagoAdelantadoCreate,
    PagoAplicacionCreate,
    PagoCreate,
)

COLUMNAS_TIPOS_PAGO = [
    "id",
    "nombre",
    "valor",
    "tipo_cobro",
    "activo",
    "mes_inicial",
    "frecuencia_meses",
    "dia_limite_mes",
    "dias_gracia",
    "mora_tipo",
    "mora_valor",
]

def fila_tipo_pago(tipo_cobro):
    """Un unico concepto de 100 asignado al curso 3 del estudiante 1."""
    return (4, "Pension", 100, tipo_cobro, True, None, 1, None, 0, None, 0)


class CursorFalso:
    """Cursor hermetico que despacha lecturas y registra escrituras."""

    def __init__(
        self,
        *,
        tipo_cobro="unico",
        venta=None,
        venta_estado="Pendiente",
        pago_existente=None,
        nombre_duplicado=False,
        historial=(),
    ):
        self.tipo_cobro = tipo_cobro
        self.venta = venta
        self.venta_estado = venta_estado
        self.pago_existente = pago_existente
        self.nombre_duplicado = nombre_duplicado
        self.historial = list(historial)
        self.ejecutadas = []
        self.filas = []
        self.cerrado = False
        self._siguiente_id = 900

    # -- infraestructura ---------------------------------------------------
    def execute(self, query, params=None):
        normalizada = " ".join(str(query).lower().split())
        self.ejecutadas.append((normalizada, params))
        self.filas = self._despachar(normalizada, params)

    def fetchall(self):
        return list(self.filas)

    def fetchone(self):
        return self.filas[0] if self.filas else None

    def close(self):
        self.cerrado = True

    # -- consultas ---------------------------------------------------------
    @property
    def escrituras(self):
        return [
            (query, params)
            for query, params in self.ejecutadas
            if query.startswith(("insert", "update", "delete"))
        ]

    def escrituras_contra(self, tabla):
        return [q for q, _ in self.escrituras if tabla in q]

    def _nuevo_id(self):
        self._siguiente_id += 1
        return self._siguiente_id

    def _despachar(self, query, params):
        # --- escrituras del dominio ---
        if query.startswith("insert into pagos_aplicaciones"):
            return [(self._nuevo_id(),)]
        if query.startswith("insert into pagos"):
            return [(self._nuevo_id(),)]
        if query.startswith("update ventas") and "returning" in query:
            total, pagado = self.venta or (0, 0)
            return [(total, pagado + float(params[0] or 0))]
        if query.startswith(("insert", "update", "delete")):
            return [(self._nuevo_id(),)]

        # --- guardas de migracion ---
        if "from pg_indexes" in query:
            return [(1,)]
        if "from information_schema.columns" in query:
            return [(columna,) for columna in COLUMNAS_TIPOS_PAGO]
        if "from information_schema.tables" in query:
            return [("pagos_aplicaciones",), ("tipos_pagos_cursos",),
                    ("tipos_pagos_estudiantes",)]
        if "pg_advisory_xact_lock" in query:
            return [(True,)]

        # --- catalogo y asignaciones ---
        if "from tipos_de_pagos" in query and "order by id" in query:
            return [fila_tipo_pago(self.tipo_cobro)]
        if "from tipos_de_pagos" in query and "lower(trim(nombre))" in query:
            return [(4,)] if self.nombre_duplicado else []
        if "select curso_id, tipo_pago_id, valor" in query:
            return [(3, 4, 100)]
        if "c.nombre as curso_nombre" in query:
            return [{
                "id": 1,
                "tipo_pago_id": 4,
                "curso_id": 3,
                "valor": 100,
                "activo": True,
                "curso_nombre": "Curso 3",
            }]
        if "from tipos_pagos_cursos" in query:
            return [(4, 100)]
        if "from tipos_pagos_estudiantes" in query:
            return []
        if "from tipos_de_pagos" in query:
            return [(4,)]
        if "select c.id" in query and "where e.id" in query:
            return [(3,)]
        if "from estudiantes" in query:
            return [{"curso_id": 3}]

        # --- pagos y ventas ---
        if "for update" in query and "from pagos" in query:
            return [self.pago_existente] if self.pago_existente else []
        if "for update" in query and "from ventas" in query:
            if self.venta is None:
                return []
            total, pagado = self.venta
            return [(7, total, pagado)]
        if "from ventas" in query:
            if self.venta is None:
                return []
            total, pagado = self.venta
            return [(total, pagado, self.venta_estado)]
        if "select count(*)" in query and "from pagos" in query:
            return [(len(self.historial),)]
        if "from pagos" in query and "order by id desc" in query:
            return list(self.historial)
        if "string_agg(distinct descripcion" in query:
            return [(0, None)]
        if "select descripcion, coalesce(sum(monto), 0)" in query:
            return []
        if "select tipo_pago, coalesce(sum(monto), 0)" in query:
            return []
        if "from pagos_aplicaciones" in query:
            return []
        if "venta_id is not null" in query:
            return [(0,)]
        if "from pagos" in query:
            return []

        raise AssertionError(f"Consulta no caracterizada: {query}")


class ConexionFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False
        self.aperturas = 0

    def cursor(self, cursor_factory=None):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


@pytest.fixture
def conexion(monkeypatch):
    """Instala una conexion hermetica y devuelve (conexion, cursor)."""

    def instalar(modulo=pagos_controller, **kwargs):
        cursor = CursorFalso(**kwargs)
        conn = ConexionFalsa(cursor)

        def abrir():
            conn.aperturas += 1
            return conn

        monkeypatch.setattr(modulo, "get_connection", abrir)
        return conn, cursor

    return instalar


# ---------------------------------------------------------------------------
# 1. Frontera HTTP
# ---------------------------------------------------------------------------

def _rutas(*routers):
    return {
        (ruta.path, metodo): ruta
        for router in routers
        for ruta in router.routes
        if isinstance(ruta, APIRoute)
        for metodo in ruta.methods
    }


def test_la_frontera_http_del_dominio_son_diecinueve_entradas_admin_sincronas():
    rutas = _rutas(rutas_pagos.router, rutas_tipos_pagos.router)

    esperadas = {
        ("/pagos", "POST"),
        ("/pagos/vencidos/opciones/{estudiante_id}", "GET"),
        ("/pagos/adelanto/opciones/{estudiante_id}", "GET"),
        ("/pagos/adelanto", "POST"),
        ("/pagos/{estudiante_id}", "GET"),
        ("/pagos/{pago_id}/anular", "POST"),
        ("/tipos-pagos", "POST"),
        ("/tipos-pagos", "GET"),
        ("/tipos-pagos/{id}", "PUT"),
        ("/tipos-pagos/{id}", "DELETE"),
        ("/tipos-pagos/detallado", "GET"),
        ("/tipos-pagos/{id}/detalle", "GET"),
        ("/tipos-pagos/{id}/configuracion", "PUT"),
        ("/tipos-pagos/{id}/cursos", "GET"),
        ("/tipos-pagos/{id}/cursos", "PUT"),
        ("/tipos-pagos/{id}/cursos/{curso_id}", "DELETE"),
        ("/estudiantes/{estudiante_id}/valores-pago-personalizados", "GET"),
        ("/estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}", "PUT"),
        ("/estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}", "DELETE"),
    }

    assert set(rutas) == esperadas
    assert len(rutas) == 19

    for (path, metodo), ruta in rutas.items():
        assert ruta.status_code is None, f"{metodo} {path} fijaba status_code"
        assert ruta.response_model is None, f"{metodo} {path} fijaba response_model"
        assert not inspect.iscoroutinefunction(ruta.endpoint), f"{metodo} {path} es async"
        assert any(
            dependencia.call is get_current_active_admin
            for dependencia in ruta.dependant.dependencies
        ), f"{metodo} {path} no exige admin"


def test_solo_estas_ocho_entradas_reciben_body():
    rutas = _rutas(rutas_pagos.router, rutas_tipos_pagos.router)
    con_body = {
        clave for clave, ruta in rutas.items() if ruta.dependant.body_params
    }

    assert con_body == {
        ("/pagos", "POST"),
        ("/pagos/adelanto", "POST"),
        ("/pagos/{pago_id}/anular", "POST"),
        ("/tipos-pagos", "POST"),
        ("/tipos-pagos/{id}", "PUT"),
        ("/tipos-pagos/{id}/configuracion", "PUT"),
        ("/tipos-pagos/{id}/cursos", "PUT"),
        ("/estudiantes/{estudiante_id}/valores-pago-personalizados/{tipo_pago_id}", "PUT"),
    }


def test_el_orden_de_las_rutas_de_pagos_protege_las_mas_especificas():
    """`/pagos/{estudiante_id}` capturaria `/pagos/adelanto` si fuera primero."""
    paths = [
        ruta.path
        for ruta in rutas_pagos.router.routes
        if isinstance(ruta, APIRoute)
    ]

    assert paths.index("/pagos/vencidos/opciones/{estudiante_id}") < paths.index(
        "/pagos/{estudiante_id}"
    )
    assert paths.index("/pagos/adelanto/opciones/{estudiante_id}") < paths.index(
        "/pagos/{estudiante_id}"
    )
    assert paths.index("/pagos/adelanto") < paths.index("/pagos/{estudiante_id}")


# ---------------------------------------------------------------------------
# 2. Contrato transaccional de las escrituras
# ---------------------------------------------------------------------------

def test_registrar_pago_simple_inserta_una_fila_y_confirma_una_vez(conexion):
    conn, cursor = conexion()
    pago = PagoCreate(estudiante_id=1, monto=100, descripcion="Pension")

    pago_id = pagos_controller.registrar_pago_controller(pago)

    assert isinstance(pago_id, int)
    assert len(cursor.escrituras_contra("insert into pagos")) == 1
    assert cursor.escrituras_contra("update ventas") == []
    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert conn.cerrada is True
    assert cursor.cerrado is True


def test_registrar_pago_con_metodos_inserta_un_pago_por_metodo_y_devuelve_lista(conexion):
    conn, cursor = conexion()
    pago = PagoCreate(
        estudiante_id=1,
        monto=100,
        descripcion="Pension",
        metodos=[
            MetodoPago(tipo="Efectivo", monto=60),
            MetodoPago(tipo="Transferencia", monto=40, nota="Nequi"),
        ],
    )

    resultado = pagos_controller.registrar_pago_controller(pago)

    assert isinstance(resultado, list) and len(resultado) == 2
    assert len(cursor.escrituras_contra("insert into pagos")) == 2
    assert conn.commits == 1


def test_el_metodo_con_nota_se_persiste_como_tipo_guion_nota(conexion):
    _conn, cursor = conexion()
    pago = PagoCreate(
        estudiante_id=1,
        monto=40,
        descripcion="Pension",
        metodos=[MetodoPago(tipo="Transferencia", monto=40, nota="Nequi")],
    )

    pagos_controller.registrar_pago_controller(pago)

    inserciones = [
        params for query, params in cursor.escrituras
        if query.startswith("insert into pagos ")
    ]
    assert inserciones[0][-1] == "Transferencia - Nequi"


def test_registrar_pago_no_es_idempotente_dos_llamadas_crean_dos_pagos(conexion):
    """Contrato actual: no hay clave de idempotencia en POST /pagos."""
    conn, cursor = conexion()
    pago = PagoCreate(estudiante_id=1, monto=50, descripcion="Pension")

    primero = pagos_controller.registrar_pago_controller(pago)
    segundo = pagos_controller.registrar_pago_controller(pago)

    assert primero != segundo
    assert len(cursor.escrituras_contra("insert into pagos")) == 2
    assert conn.commits == 2


def test_registrar_pago_rechaza_monto_mayor_a_la_deuda_sin_escribir(conexion):
    conn, cursor = conexion()
    pago = PagoCreate(estudiante_id=1, monto=100000, descripcion="Pension")

    with pytest.raises(ValueError, match="no puede ser mayor a la deuda"):
        pagos_controller.registrar_pago_controller(pago)

    assert cursor.escrituras == []
    assert conn.commits == 0
    assert conn.rollbacks == 1
    assert conn.cerrada is True


def test_registrar_pago_rechaza_monto_cero_sin_escribir(conexion):
    conn, cursor = conexion()
    pago = PagoCreate(estudiante_id=1, monto=0, descripcion="Pension")

    with pytest.raises(ValueError, match="mayor a cero"):
        pagos_controller.registrar_pago_controller(pago)

    assert cursor.escrituras == []
    assert conn.rollbacks == 1


def test_el_pago_de_una_venta_abona_el_saldo_y_cierra_la_venta_al_cubrirla(conexion):
    conn, cursor = conexion(venta=(100, 0))
    pago = PagoCreate(estudiante_id=1, monto=100, venta_id=7, descripcion="Cargo #7")

    pagos_controller.registrar_pago_controller(pago)

    actualizaciones = cursor.escrituras_contra("update ventas")
    assert len(actualizaciones) == 2
    assert "pagado = coalesce(pagado, 0) + %s" in actualizaciones[0]
    assert "estado = 'pagado'" in actualizaciones[1]
    assert conn.commits == 1


def test_anular_pago_exige_motivo_de_cinco_caracteres_antes_de_conectar(conexion):
    conn, cursor = conexion()

    with pytest.raises(ValueError, match="al menos 5 caracteres"):
        pagos_controller.anular_pago_controller(1, "no", 99)

    assert conn.aperturas == 0
    assert cursor.ejecutadas == []
    assert conn.rollbacks == 0


def test_anular_pago_bloquea_con_for_update_y_desactiva_sus_aplicaciones(conexion):
    conn, cursor = conexion(pago_existente=(5, "Pagado", 100.0, None, "Pension"))

    resultado = pagos_controller.anular_pago_controller(5, "Pago duplicado", 99)

    assert resultado == {"mensaje": "Pago anulado correctamente", "pago_id": 5}
    lecturas = [q for q, _ in cursor.ejecutadas if "for update" in q]
    assert any("from pagos" in q for q in lecturas)
    assert cursor.escrituras_contra("update pagos_aplicaciones")
    assert any(
        "set activo = false" in q
        for q in cursor.escrituras_contra("update pagos_aplicaciones")
    )
    assert any(
        "estado = 'anulado'" in q for q in cursor.escrituras_contra("update pagos")
    )
    assert conn.commits == 1
    assert conn.cerrada is True


def test_anular_un_pago_ya_anulado_falla_y_revierte(conexion):
    conn, cursor = conexion(pago_existente=(5, "  ANULADO  ", 100.0, None, "Pension"))

    with pytest.raises(ValueError, match="ya est[aá] anulado"):
        pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    assert cursor.escrituras == []
    assert conn.commits == 0
    assert conn.rollbacks == 1


def test_anular_un_pago_inexistente_falla_y_revierte(conexion):
    conn, cursor = conexion(pago_existente=None)

    with pytest.raises(ValueError, match="no existe"):
        pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    assert cursor.escrituras == []
    assert conn.rollbacks == 1


def test_anular_un_pago_de_venta_devuelve_el_saldo_y_reabre_la_venta(conexion):
    conn, cursor = conexion(
        pago_existente=(5, "Pagado", 100.0, 7, "Cargo #7"),
        venta=(100, 100),
    )

    pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    actualizaciones = [
        params for query, params in cursor.escrituras if "update ventas" in query
    ]
    assert actualizaciones[0][0] == 0.0
    assert actualizaciones[0][1] == "Pendiente"
    assert conn.commits == 1


# ---------------------------------------------------------------------------
# 3. Pagos adelantados: bloqueo, distribucion e IntegrityError
# ---------------------------------------------------------------------------

def test_el_adelanto_toma_un_advisory_lock_de_transaccion_antes_de_escribir(conexion):
    conn, cursor = conexion(tipo_cobro="mensual")
    pago = PagoAdelantadoCreate(
        estudiante_id=1,
        tipo_pago_id=4,
        cantidad_meses=1,
        metodos=[MetodoPago(tipo="Efectivo", monto=100)],
    )

    pagos_controller.registrar_pago_adelantado_controller(pago, hoy=date(2026, 1, 15))

    indice_lock = next(
        i for i, (q, _) in enumerate(cursor.ejecutadas) if "pg_advisory_xact_lock" in q
    )
    indice_insert = next(
        i for i, (q, _) in enumerate(cursor.ejecutadas) if q.startswith("insert into pagos ")
    )
    assert indice_lock < indice_insert
    assert conn.commits == 1


def test_el_adelanto_traduce_integrityerror_a_un_mensaje_de_negocio(conexion, monkeypatch):
    conn, cursor = conexion(tipo_cobro="mensual")
    original = cursor.execute

    def execute_que_choca(query, params=None):
        if str(query).strip().lower().startswith("insert into pagos_aplicaciones"):
            raise IntegrityError("duplicate key")
        return original(query, params)

    monkeypatch.setattr(cursor, "execute", execute_que_choca)
    pago = PagoAdelantadoCreate(
        estudiante_id=1,
        tipo_pago_id=4,
        cantidad_meses=1,
        metodos=[MetodoPago(tipo="Efectivo", monto=100)],
    )

    with pytest.raises(ValueError, match="ya tiene un pago adelantado"):
        pagos_controller.registrar_pago_adelantado_controller(pago, hoy=date(2026, 1, 15))

    assert conn.commits == 0
    assert conn.rollbacks == 1
    assert conn.cerrada is True


def test_el_adelanto_exige_que_los_metodos_sumen_el_total(conexion):
    conn, cursor = conexion(tipo_cobro="mensual")
    pago = PagoAdelantadoCreate(
        estudiante_id=1,
        tipo_pago_id=4,
        cantidad_meses=1,
        metodos=[MetodoPago(tipo="Efectivo", monto=55)],
    )

    with pytest.raises(ValueError, match="debe ser igual"):
        pagos_controller.registrar_pago_adelantado_controller(pago, hoy=date(2026, 1, 15))

    assert cursor.escrituras == []
    assert conn.rollbacks == 1


def test_las_cuotas_de_un_pago_normal_exigen_el_indice_parcial(conexion):
    """Sin `uq_pagos_aplicaciones_pago_periodo_activas` el flujo se detiene."""
    conn, cursor = conexion(tipo_cobro="mensual")

    def sin_indice(query, params=None):
        normalizada = " ".join(str(query).lower().split())
        cursor.ejecutadas.append((normalizada, params))
        cursor.filas = [] if "from pg_indexes" in normalizada else cursor._despachar(
            normalizada, params
        )

    cursor.execute = sin_indice
    pago = PagoCreate(
        estudiante_id=1,
        monto=100,
        descripcion="Pension",
        aplicaciones=[
            PagoAplicacionCreate(tipo_pago_id=4, periodo=date(2026, 1, 1), monto=100)
        ],
    )

    with pytest.raises(pagos_controller.MigracionPagosAdelantadosPendienteError):
        pagos_controller.registrar_pago_controller(pago)

    assert cursor.escrituras == []
    assert conn.rollbacks == 1


# ---------------------------------------------------------------------------
# 4. Tipos de pago: idempotencia, ciclo de vida y errores absorbidos
# ---------------------------------------------------------------------------

def test_eliminar_tipo_pago_nunca_toca_la_base_y_la_ruta_responde_405():
    resultado = tipos_pagos_controller.eliminar_tipo_pago(1)

    assert "error" in resultado
    assert "no se eliminan fisicamente" in resultado["error"]


def test_crear_tipo_pago_duplicado_no_inserta_y_revierte(conexion):
    conn, cursor = conexion(modulo=tipos_pagos_controller, nombre_duplicado=True)

    with pytest.raises(tipos_pagos_controller.TipoPagoDuplicadoError):
        tipos_pagos_controller.crear_tipo_pago("Pension", 100)

    assert cursor.escrituras_contra("insert into tipos_de_pagos") == []
    assert conn.commits == 0
    assert conn.rollbacks == 1
    assert conn.cerrada is True


def test_un_fallo_de_infraestructura_al_crear_se_absorbe_y_devuelve_none(conexion):
    """Rareza conservada: la ruta lo convierte en 400, no en 500."""
    conn, cursor = conexion(modulo=tipos_pagos_controller)
    original = cursor.execute

    def execute_que_falla(query, params=None):
        if str(query).strip().lower().startswith("insert into tipos_de_pagos"):
            raise RuntimeError("conexion perdida")
        return original(query, params)

    cursor.execute = execute_que_falla
    cursor.filas = []

    resultado = tipos_pagos_controller.crear_tipo_pago("Matricula", 100)

    assert resultado is None
    assert conn.commits == 0
    assert conn.rollbacks == 1


def test_el_upsert_de_cursos_asignados_es_idempotente_por_on_conflict(conexion):
    conn, cursor = conexion(modulo=tipos_pagos_controller)

    resultado = tipos_pagos_controller.upsert_cursos_asignados(
        4, [{"curso_id": 3, "valor": 100}]
    )

    inserciones = cursor.escrituras_contra("insert into tipos_pagos_cursos")
    assert len(inserciones) == 1
    assert "on conflict (tipo_pago_id, curso_id) do update" in inserciones[0]
    assert cursor.escrituras_contra("delete from tipos_pagos_cursos")
    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert resultado is not None


def test_el_upsert_de_cursos_reemplaza_el_estado_borrando_los_ausentes(conexion):
    _conn, cursor = conexion(modulo=tipos_pagos_controller)

    tipos_pagos_controller.upsert_cursos_asignados(4, [])

    borrados = [
        params for query, params in cursor.escrituras
        if "delete from tipos_pagos_cursos" in query
    ]
    assert borrados == [(4,)]


def test_el_upsert_de_valores_personalizados_es_idempotente_por_on_conflict(conexion):
    conn, cursor = conexion(modulo=tipos_pagos_controller)

    tipos_pagos_controller.upsert_valor_personalizado_estudiante(1, 4, 80)

    inserciones = cursor.escrituras_contra("insert into tipos_pagos_estudiantes")
    assert len(inserciones) == 1
    assert "on conflict (tipo_pago_id, estudiante_id) do update" in inserciones[0]
    assert conn.commits == 1


def test_el_upsert_de_valores_exige_que_el_concepto_este_asignado_al_curso(conexion):
    conn, cursor = conexion(modulo=tipos_pagos_controller)
    original = cursor.execute

    def sin_asignacion(query, params=None):
        normalizada = " ".join(str(query).lower().split())
        if "from tipos_pagos_cursos" in normalizada and "activo = true" in normalizada:
            cursor.ejecutadas.append((normalizada, params))
            cursor.filas = []
            return None
        return original(query, params)

    cursor.execute = sin_asignacion

    with pytest.raises(ValueError, match="no esta asignado al curso"):
        tipos_pagos_controller.upsert_valor_personalizado_estudiante(1, 4, 80)

    assert cursor.escrituras_contra("insert into tipos_pagos_estudiantes") == []
    assert conn.rollbacks == 1


def test_eliminar_un_valor_personalizado_lo_desactiva_en_vez_de_borrarlo(conexion):
    conn, cursor = conexion(modulo=tipos_pagos_controller)

    assert tipos_pagos_controller.eliminar_valor_personalizado_estudiante(1, 4) is True

    actualizaciones = cursor.escrituras_contra("update tipos_pagos_estudiantes")
    assert len(actualizaciones) == 1
    assert "set activo = false" in actualizaciones[0]
    assert cursor.escrituras_contra("delete from tipos_pagos_estudiantes") == []
    assert conn.commits == 1


# ---------------------------------------------------------------------------
# 5. Lo que la capa 4 lee y esta capa escribe
# ---------------------------------------------------------------------------

def test_ninguna_escritura_del_dominio_menciona_pagos_concepto_id(conexion):
    """La columna no existe. La capa 4 lo demostro; 5.0 lo congela."""
    _conn, cursor = conexion()
    pago = PagoCreate(estudiante_id=1, monto=100, descripcion="Pension")

    pagos_controller.registrar_pago_controller(pago)

    assert not any("concepto_id" in query for query, _ in cursor.ejecutadas)


def test_el_pago_normal_persiste_concepto_en_descripcion_y_medio_en_tipo_pago(conexion):
    _conn, cursor = conexion()
    pago = PagoCreate(
        estudiante_id=1,
        monto=100,
        descripcion="Pension",
        metodos=[MetodoPago(tipo="Efectivo", monto=100)],
    )

    pagos_controller.registrar_pago_controller(pago)

    query, params = next(
        (q, p) for q, p in cursor.escrituras if q.startswith("insert into pagos ")
    )
    assert "(estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago)" in query
    assert params[3] == "Pension"
    assert params[5] == "Efectivo"


def test_el_adelanto_escribe_una_descripcion_compuesta_que_no_es_el_concepto(conexion):
    """Por eso la capa 4 excluye del agrupado por descripcion los pagos aplicados."""
    _conn, cursor = conexion(tipo_cobro="mensual")
    pago = PagoAdelantadoCreate(
        estudiante_id=1,
        tipo_pago_id=4,
        cantidad_meses=1,
        metodos=[MetodoPago(tipo="Efectivo", monto=100)],
    )

    pagos_controller.registrar_pago_adelantado_controller(pago, hoy=date(2026, 1, 15))

    _query, params = next(
        (q, p) for q, p in cursor.escrituras if q.startswith("insert into pagos ")
    )
    descripcion = params[2]
    assert descripcion.startswith("Pension · Pago adelantado: ")
    assert descripcion != "Pension"
    assert cursor.escrituras_contra("insert into pagos_aplicaciones")


def test_la_anulacion_escribe_el_estado_que_la_capa_4_excluye_de_los_totales(conexion):
    _conn, cursor = conexion(pago_existente=(5, "Pagado", 100.0, None, "Pension"))

    pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    query, params = next(
        (q, p) for q, p in cursor.escrituras
        if q.startswith("update pagos") and "estado = 'anulado'" in q
    )
    assert "motivo_anulacion = %s" in query
    assert "fecha_anulacion = %s" in query
    assert "anulado_por = %s" in query
    assert params[0] == "Motivo valido"
    assert isinstance(params[1], datetime)
    assert params[1].tzinfo is None
    assert params[2] == 99


# ---------------------------------------------------------------------------
# 6. Linea base de consultas y ciclo de vida de la conexion
# ---------------------------------------------------------------------------

def test_linea_base_del_pago_simple_es_lock_once_lecturas_y_una_escritura(conexion):
    """Un lock, once lecturas para recalcular la deuda entera y una escritura."""
    _conn, cursor = conexion()

    pagos_controller.registrar_pago_controller(
        PagoCreate(estudiante_id=1, monto=100, descripcion="Pension")
    )

    assert len(cursor.ejecutadas) == 13
    assert len(cursor.escrituras) == 1


def test_cada_metodo_adicional_suma_exactamente_una_escritura(conexion):
    _conn, cursor = conexion()

    pagos_controller.registrar_pago_controller(
        PagoCreate(
            estudiante_id=1,
            monto=100,
            descripcion="Pension",
            metodos=[
                MetodoPago(tipo="Efectivo", monto=60),
                MetodoPago(tipo="Transferencia", monto=40),
            ],
        )
    )

    assert len(cursor.ejecutadas) == 14
    assert len(cursor.escrituras) == 2


def test_el_pago_de_venta_no_recalcula_la_deuda_academica(conexion):
    """Rareza util: el camino de venta sale antes y cuesta 5 sentencias, no 13."""
    _conn, cursor = conexion(venta=(100, 0))

    pagos_controller.registrar_pago_controller(
        PagoCreate(estudiante_id=1, monto=100, venta_id=7, descripcion="Cargo #7")
    )

    assert len(cursor.ejecutadas) == 5
    assert len(cursor.escrituras) == 3


def test_linea_base_de_la_anulacion(conexion):
    _conn, cursor = conexion(pago_existente=(5, "Pagado", 100.0, None, "Pension"))

    pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    assert len(cursor.ejecutadas) == 4
    assert len(cursor.escrituras) == 2


def test_linea_base_de_la_anulacion_con_venta(conexion):
    _conn, cursor = conexion(
        pago_existente=(5, "Pagado", 100.0, 7, "Cargo #7"),
        venta=(100, 100),
    )

    pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    assert len(cursor.ejecutadas) == 6
    assert len(cursor.escrituras) == 3


def test_linea_base_del_adelanto_de_un_mes(conexion):
    _conn, cursor = conexion(tipo_cobro="mensual")

    pagos_controller.registrar_pago_adelantado_controller(
        PagoAdelantadoCreate(
            estudiante_id=1,
            tipo_pago_id=4,
            cantidad_meses=1,
            metodos=[MetodoPago(tipo="Efectivo", monto=100)],
        ),
        hoy=date(2026, 1, 15),
    )

    assert len(cursor.ejecutadas) == 12
    assert len(cursor.escrituras) == 2


def test_las_lecturas_de_opciones_no_escriben_ni_confirman(conexion):
    conn, cursor = conexion(tipo_cobro="mensual")

    pagos_controller.obtener_opciones_adelanto_controller(1, hoy=date(2026, 1, 15))

    assert len(cursor.ejecutadas) == 9
    assert cursor.escrituras == []
    assert conn.commits == 0
    assert conn.rollbacks == 0
    assert conn.cerrada is True


def test_el_upsert_de_cursos_usa_una_sola_conexion(conexion):
    """Antes releia el estado con `get_connection` propio, sosteniendo dos.

    Las dos se solapaban, porque el `return` se evalua antes del `finally`. Peor
    aun: si la relectura fallaba tras el `commit`, el `except` devolvia None y la
    ruta respondia 400 sobre una escritura ya guardada.
    """
    conn, _cursor = conexion(modulo=tipos_pagos_controller)

    tipos_pagos_controller.upsert_cursos_asignados(4, [{"curso_id": 3, "valor": 100}])

    assert conn.aperturas == 1
    assert conn.commits == 1


def test_el_upsert_de_valores_personalizados_usa_una_sola_conexion(conexion):
    conn, cursor = conexion(modulo=tipos_pagos_controller)

    tipos_pagos_controller.upsert_valor_personalizado_estudiante(1, 4, 80)

    assert conn.aperturas == 1
    assert len(cursor.escrituras) == 1
    assert conn.commits == 1


def test_la_relectura_del_upsert_ocurre_antes_del_commit(conexion):
    """Asi devuelve lo que esta peticion escribio, no lo que haya despues."""
    _conn, cursor = conexion(modulo=tipos_pagos_controller)

    tipos_pagos_controller.upsert_cursos_asignados(4, [{"curso_id": 3, "valor": 100}])

    indice_insert = next(
        i for i, (q, _) in enumerate(cursor.ejecutadas)
        if q.startswith("insert into tipos_pagos_cursos")
    )
    indice_relectura = next(
        i for i, (q, _) in enumerate(cursor.ejecutadas)
        if "c.nombre as curso_nombre" in q
    )
    assert indice_insert < indice_relectura


# ---------------------------------------------------------------------------
# 7. Lecturas de `pagos` y contacto con `ventas`, caracterizados antes de 5.2
# ---------------------------------------------------------------------------

FILA_HISTORIAL = (
    7, 11, 150000, datetime(2026, 8, 3, 14, 30), "Pension agosto",
    "Efectivo", "Pagado", None, None, None,
)


def test_el_historial_paginado_cuenta_primero_y_luego_lee_la_pagina(conexion):
    conn, cursor = conexion(historial=[FILA_HISTORIAL])

    resultado = pagos_controller.historial_pagos_paginado_controller(
        11, limit=25, offset=50
    )

    assert len(cursor.ejecutadas) == 2
    conteo, pagina = cursor.ejecutadas
    assert conteo[0].startswith("select count(*)")
    assert conteo[1] == (11,)
    assert "limit %s offset %s" in pagina[0]
    assert pagina[1] == (11, 25, 50)
    assert resultado["total"] == 1
    assert resultado["limit"] == 25
    assert resultado["offset"] == 50
    assert resultado["items"][0]["pago_id"] == 7


def test_el_historial_paginado_es_lector_y_no_confirma_ni_revierte(conexion):
    conn, cursor = conexion(historial=[FILA_HISTORIAL])

    pagos_controller.historial_pagos_paginado_controller(11, limit=10, offset=0)

    assert cursor.escrituras == []
    assert conn.commits == 0
    assert conn.rollbacks == 0
    assert conn.cerrada is True
    assert cursor.cerrado is True


def test_las_dos_lecturas_del_paginado_ordenan_igual_que_el_historial(conexion):
    _conn, cursor = conexion(historial=[FILA_HISTORIAL])

    pagos_controller.historial_pagos_paginado_controller(11, limit=10, offset=0)

    _conteo, pagina = cursor.ejecutadas
    assert "order by id desc" in pagina[0]
    assert "coalesce(estado, 'pagado') as estado" in pagina[0]


def test_el_saldo_de_venta_se_lee_antes_de_insertar_el_pago(conexion):
    _conn, cursor = conexion(venta=(100, 40))

    pagos_controller.registrar_pago_controller(
        PagoCreate(estudiante_id=1, monto=60, venta_id=7, descripcion="Cargo #7")
    )

    assert "pg_advisory_xact_lock" in cursor.ejecutadas[0][0]
    lectura, params = cursor.ejecutadas[1]
    assert lectura.startswith("select total, coalesce(pagado, 0), estado from ventas")
    assert params == (7,)


def test_un_cargo_de_inventario_inexistente_se_rechaza_sin_escribir(conexion):
    conn, cursor = conexion(venta=None)

    with pytest.raises(ValueError, match="no existe"):
        pagos_controller.registrar_pago_controller(
            PagoCreate(estudiante_id=1, monto=60, venta_id=7, descripcion="Cargo #7")
        )

    assert cursor.escrituras == []
    assert conn.rollbacks == 1


def test_un_cargo_ya_pagado_se_rechaza_sin_escribir(conexion):
    conn, cursor = conexion(venta=(100, 100), venta_estado="Pagado")

    with pytest.raises(ValueError, match="ya no tiene saldo pendiente"):
        pagos_controller.registrar_pago_controller(
            PagoCreate(estudiante_id=1, monto=10, venta_id=7, descripcion="Cargo #7")
        )

    assert cursor.escrituras == []
    assert conn.rollbacks == 1


def test_pagar_de_mas_un_cargo_de_inventario_se_rechaza_sin_escribir(conexion):
    conn, cursor = conexion(venta=(100, 40))

    with pytest.raises(ValueError, match="no puede ser mayor al saldo pendiente"):
        pagos_controller.registrar_pago_controller(
            PagoCreate(estudiante_id=1, monto=61, venta_id=7, descripcion="Cargo #7")
        )

    assert cursor.escrituras == []
    assert conn.rollbacks == 1


def test_el_abono_a_la_venta_no_la_cierra_si_queda_saldo(conexion):
    _conn, cursor = conexion(venta=(100, 0))

    pagos_controller.registrar_pago_controller(
        PagoCreate(estudiante_id=1, monto=40, venta_id=7, descripcion="Cargo #7")
    )

    actualizaciones = cursor.escrituras_contra("update ventas")
    assert len(actualizaciones) == 1
    assert "pagado = coalesce(pagado, 0) + %s" in actualizaciones[0]
    assert not any("estado = 'pagado'" in q for q in actualizaciones)


def test_la_anulacion_bloquea_la_venta_con_for_update_antes_de_devolver_el_saldo(conexion):
    _conn, cursor = conexion(
        pago_existente=(5, "Pagado", 100.0, 7, "Cargo #7"),
        venta=(100, 100),
    )

    pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    indice_lock = next(
        i for i, (q, _) in enumerate(cursor.ejecutadas)
        if "from ventas" in q and "for update" in q
    )
    indice_update = next(
        i for i, (q, _) in enumerate(cursor.ejecutadas) if "update ventas" in q
    )
    assert indice_lock < indice_update


def test_la_lectura_de_bloqueo_del_pago_trae_las_cinco_columnas_que_usa(conexion):
    _conn, cursor = conexion(pago_existente=(5, "Pagado", 100.0, None, "Pension"))

    pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    lectura, params = cursor.ejecutadas[0]
    assert "select id, coalesce(estado, 'pagado'), monto, venta_id, descripcion" in lectura
    assert "from pagos where id = %s for update" in lectura
    assert params == (5,)


def test_un_pago_heredado_con_cargo_solo_en_el_texto_recupera_su_venta_id(conexion):
    _conn, cursor = conexion(
        pago_existente=(5, "Pagado", 100.0, None, "Abono Cargo #42"),
        venta=(100, 100),
    )

    pagos_controller.anular_pago_controller(5, "Motivo valido", 99)

    asignaciones = [
        params for query, params in cursor.escrituras
        if "update pagos set venta_id" in query
    ]
    assert asignaciones == [(42, 5)]


# ---------------------------------------------------------------------------
# 8. Lectura de aplicaciones vigentes, caracterizada antes de 5.3
# ---------------------------------------------------------------------------

CONCEPTO_MENSUAL = {
    "id": 4,
    "nombre": "Pension",
    "valor_unitario": 100.0,
    "mes_inicial": None,
    "frecuencia_meses": 1,
}


def test_los_periodos_disponibles_solo_suman_aplicaciones_activas_no_anuladas(conexion):
    _conn, cursor = conexion()

    pagos_controller._periodos_disponibles(
        cursor, 11, CONCEPTO_MENSUAL, date(2026, 10, 15)
    )

    consulta, params = cursor.ejecutadas[0]
    assert "select pa.periodo, coalesce(sum(pa.monto), 0)" in consulta
    assert "from pagos_aplicaciones pa join pagos p on p.id = pa.pago_id" in consulta
    assert "pa.activo = true" in consulta
    assert "coalesce(p.estado, 'pagado') <> 'anulado'" in consulta
    assert "group by pa.periodo" in consulta
    assert params == (11, 4)


def test_los_periodos_disponibles_emiten_una_sola_consulta(conexion):
    _conn, cursor = conexion()

    pagos_controller._periodos_disponibles(
        cursor, 11, CONCEPTO_MENSUAL, date(2026, 10, 15)
    )

    assert len(cursor.ejecutadas) == 1
    assert cursor.escrituras == []


def test_sin_aplicaciones_previas_todo_mes_futuro_queda_disponible(conexion):
    _conn, cursor = conexion()

    periodos = pagos_controller._periodos_disponibles(
        cursor, 11, CONCEPTO_MENSUAL, date(2026, 10, 15)
    )

    assert [p["periodo"] for p in periodos] == [date(2026, 11, 1), date(2026, 12, 1)]
    assert all(p["saldo"] == 100.0 for p in periodos)
    assert all(p["estado"] == "disponible" for p in periodos)


# ---------------------------------------------------------------------------
# 9. Duplicados de POST /pagos
#
# El doble de arriba no modela la tabla `pagos`: sus sumas devuelven siempre
# vacio, asi que la deuda nunca baja. Sirve para contar consultas, pero no puede
# demostrar nada sobre duplicados. Estas pruebas usan un doble que si acumula lo
# insertado, de modo que la segunda llamada ve la primera.
# ---------------------------------------------------------------------------

class CursorConEstado(CursorFalso):
    """Cursor que recuerda los pagos insertados y los suma al recalcular deuda."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pagos = []

    def _despachar(self, query, params):
        if query.startswith("insert into pagos "):
            self.pagos.append((float(params[2]), params[3], params[5]))
            return [(self._nuevo_id(),)]
        if "coalesce(sum(monto), 0)" in query and "from pagos" in query:
            por_descripcion = "descripcion" in query.split("group by")[-1]
            acumulado = {}
            for monto, descripcion, tipo_pago in self.pagos:
                clave = ((descripcion if por_descripcion else tipo_pago) or "").lower()
                acumulado[clave] = acumulado.get(clave, 0.0) + monto
            return [(1, clave, monto) for clave, monto in acumulado.items()]
        return super()._despachar(query, params)


@pytest.fixture
def conexion_con_estado(monkeypatch):
    def instalar(**kwargs):
        cursor = CursorConEstado(**kwargs)
        conn = ConexionFalsa(cursor)
        monkeypatch.setattr(pagos_controller, "get_connection", lambda: conn)
        return conn, cursor

    return instalar


def _pagar(monto):
    return PagoCreate(estudiante_id=1, monto=monto, descripcion="Pension")


def test_un_duplicado_que_cubre_la_deuda_entera_se_rechaza(conexion_con_estado):
    """Proteccion accidental: la validacion de deuda relee lo ya pagado."""
    _conn, cursor = conexion_con_estado()

    pagos_controller.registrar_pago_controller(_pagar(100))

    with pytest.raises(ValueError, match=r"no puede ser mayor a la deuda pendiente"):
        pagos_controller.registrar_pago_controller(_pagar(100))

    assert len(cursor.pagos) == 1


def test_dos_pagos_parciales_identicos_se_aceptan_los_dos(conexion_con_estado):
    """Hueco conocido: el servidor no distingue duplicado de segunda cuota."""
    _conn, cursor = conexion_con_estado()

    pagos_controller.registrar_pago_controller(_pagar(50))
    pagos_controller.registrar_pago_controller(_pagar(50))

    assert len(cursor.pagos) == 2
    assert sum(monto for monto, _d, _t in cursor.pagos) == 100


def test_el_tercer_parcial_se_rechaza_cuando_ya_no_cabe_en_la_deuda(conexion_con_estado):
    _conn, cursor = conexion_con_estado()

    pagos_controller.registrar_pago_controller(_pagar(40))
    pagos_controller.registrar_pago_controller(_pagar(40))

    with pytest.raises(ValueError, match=r"no puede ser mayor a la deuda pendiente"):
        pagos_controller.registrar_pago_controller(_pagar(40))

    assert sum(monto for monto, _d, _t in cursor.pagos) == 80


def test_registrar_pago_toma_un_advisory_lock_por_estudiante_antes_de_leer_la_deuda(conexion):
    """Sin este lock la proteccion anterior no sobrevive a dos peticiones a la vez.

    Ambas leerian la deuda antes de que ninguna confirmara, las dos pasarian la
    validacion y las dos insertarian. El lock serializa leer-validar-escribir.
    """
    _conn, cursor = conexion()

    pagos_controller.registrar_pago_controller(_pagar(100))

    indice_lock = next(
        (i for i, (q, _) in enumerate(cursor.ejecutadas) if "pg_advisory_xact_lock" in q),
        None,
    )
    assert indice_lock is not None, "el camino de pago normal no toma ningun lock"

    indice_insert = next(
        i for i, (q, _) in enumerate(cursor.ejecutadas) if q.startswith("insert into pagos ")
    )
    assert indice_lock < indice_insert
    assert indice_lock == 0, "el lock debe tomarse antes de leer la deuda"


# ---------------------------------------------------------------------------
# 10. Los fallos que se absorben quedan registrados
#
# Las siete funciones de tipos de pago siguen capturando `Exception` y
# devolviendo None/False, y las rutas siguen traduciendo eso a 400 o 404: el
# contrato no cambia. Lo que cambia es que la excepcion ya no desaparece sin
# rastro. Sin estas pruebas, quitar el registro no rompe nada visible.
# ---------------------------------------------------------------------------

def _romper_en(cursor, prefijo):
    """Hace fallar la primera sentencia que empiece por `prefijo`."""
    original = cursor.execute

    def execute(query, params=None):
        if " ".join(str(query).lower().split()).startswith(prefijo):
            raise RuntimeError("conexion perdida")
        return original(query, params)

    cursor.execute = execute


def test_un_fallo_absorbido_al_crear_queda_en_el_log_con_traceback(conexion, caplog):
    conn, cursor = conexion(modulo=tipos_pagos_controller)
    _romper_en(cursor, "insert into tipos_de_pagos")

    with caplog.at_level("ERROR", logger="app.controllers.tipos_pagos_controller"):
        resultado = tipos_pagos_controller.crear_tipo_pago("Matricula", 100)

    assert resultado is None
    assert conn.rollbacks == 1
    registro = caplog.records[-1]
    assert registro.levelname == "ERROR"
    assert registro.exc_info is not None, "el traceback debe conservarse"
    assert "crear el tipo de pago" in registro.getMessage()


def test_un_fallo_absorbido_al_asignar_cursos_identifica_el_tipo_de_pago(conexion, caplog):
    _conn, cursor = conexion(modulo=tipos_pagos_controller)
    _romper_en(cursor, "delete from tipos_pagos_cursos")

    with caplog.at_level("ERROR", logger="app.controllers.tipos_pagos_controller"):
        resultado = tipos_pagos_controller.upsert_cursos_asignados(
            4, [{"curso_id": 3, "valor": 100}]
        )

    assert resultado is None
    assert "4" in caplog.records[-1].getMessage()


def test_el_error_de_dominio_no_se_registra_porque_no_es_un_fallo(conexion, caplog):
    """Un nombre duplicado es una respuesta valida, no un incidente."""
    conexion(modulo=tipos_pagos_controller, nombre_duplicado=True)

    with caplog.at_level("ERROR", logger="app.controllers.tipos_pagos_controller"):
        with pytest.raises(tipos_pagos_controller.TipoPagoDuplicadoError):
            tipos_pagos_controller.crear_tipo_pago("Pension", 100)

    assert caplog.records == []


def test_las_siete_funciones_que_absorben_excepciones_registran_el_fallo():
    """Guardia estructural: si alguien anade un `except Exception` mudo, falla."""
    import ast
    import inspect

    fuente = inspect.getsource(tipos_pagos_controller)
    mudos = []
    for nodo in ast.walk(ast.parse(fuente)):
        if not isinstance(nodo, ast.FunctionDef):
            continue
        for manejador in [h for h in ast.walk(nodo) if isinstance(h, ast.ExceptHandler)]:
            captura_todo = manejador.type is None or (
                isinstance(manejador.type, ast.Name) and manejador.type.id == "Exception"
            )
            registra = any(
                "logger." in ast.unparse(sentencia) for sentencia in manejador.body
            )
            relanza = any(isinstance(s, ast.Raise) for s in manejador.body)
            if captura_todo and not registra and not relanza:
                mudos.append(nodo.name)

    assert mudos == [], f"absorben excepciones sin registrarlas: {sorted(set(mudos))}"
