from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.controllers import tipos_pagos_controller
from app.routes import tipos_pagos as rutas_tipos_pagos
from app.services import cobros


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20260910_tipos_pagos_mes_final.sql"
ESQUEMA_BASE = RAIZ / "migrations" / "base" / "20260813_esquema_base_tenant.sql"


class CursorConfiguracion:
    def __init__(self, *, columnas, configuracion=("mensual", 2, 12)):
        self.columnas = list(columnas)
        self.configuracion = configuracion
        self.filas = []
        self.ejecutadas = []
        self.closed = False

    def execute(self, query, params=None):
        normalizada = " ".join(str(query).lower().split())
        self.ejecutadas.append((normalizada, params))
        if "from information_schema.columns" in normalizada:
            self.filas = [(columna,) for columna in self.columnas]
        elif normalizada.startswith("select tipo_cobro, mes_inicial, mes_final"):
            self.filas = [self.configuracion]
        elif normalizada.startswith("update tipos_de_pagos"):
            self.filas = [(params[-1],)]
        else:
            raise AssertionError(f"Consulta no caracterizada: {normalizada}")

    def fetchall(self):
        return list(self.filas)

    def fetchone(self):
        return self.filas[0] if self.filas else None

    def close(self):
        self.closed = True


class ConexionConfiguracion:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class CursorCobros:
    def __init__(self):
        self.paso = 0
        self.consultas = []

    def execute(self, query, params=None):
        self.consultas.append(" ".join(str(query).split()))
        self.paso += 1

    def fetchall(self):
        if self.paso == 1:
            return [
                ("id",),
                ("nombre",),
                ("valor",),
                ("tipo_cobro",),
                ("activo",),
                ("mes_inicial",),
                ("frecuencia_meses",),
                ("dia_limite_mes",),
                ("dias_gracia",),
                ("mora_tipo",),
                ("mora_valor",),
            ]
        return [(4, "Pension", 100, "mensual", True, 2, 12, 1, 5, 0, None, 0)]


def test_schema_usa_diciembre_por_defecto_y_valida_el_rango():
    config = rutas_tipos_pagos.ConfiguracionTipoPago(activo=True)

    assert config.mes_final == 12
    assert config.model_dump(exclude_unset=True) == {"activo": True}

    with pytest.raises(ValidationError, match="mes final no puede ser anterior"):
        rutas_tipos_pagos.ConfiguracionTipoPago(
            tipo_cobro="mensual",
            mes_inicial=2,
            mes_final=1,
        )

    no_mensual = rutas_tipos_pagos.ConfiguracionTipoPago(
        tipo_cobro="unico",
        mes_inicial=2,
        mes_final=1,
    )
    assert no_mensual.mes_final == 1


def test_lecturas_legacy_exponen_mes_final_diciembre_sin_la_columna():
    serializado = tipos_pagos_controller._serializar_tipo(
        {"id": 4, "nombre": "Pension", "valor": 100},
        {"id", "nombre", "valor"},
    )
    assert serializado["mes_final"] == 12

    cursor = CursorCobros()
    tipos = cobros.obtener_tipos_pago(cursor)

    assert tipos[0]["mes_final"] == 12
    assert "12 AS mes_final" in cursor.consultas[1]


def test_cobros_propaga_mes_final_al_calculo_de_cartera():
    resultado = cobros._calcular_deudas(
        tipos_pago=[{
            "id": 4,
            "nombre": "Pension",
            "valor": 100,
            "tipo_cobro": "mensual",
            "activo": True,
            "mes_inicial": 2,
            "mes_final": 11,
            "frecuencia_meses": 1,
            "dia_limite_mes": 1,
            "dias_gracia": 0,
            "mora_tipo": None,
            "mora_valor": 0,
        }],
        asignaciones_curso={4: 100},
        pagos_nombre={},
        pagos_descripcion={},
        hoy=date(2026, 12, 31),
    )

    assert resultado["deudas"][0]["cuotas_vencidas"] == 10
    assert resultado["deudas"][0]["valor_total"] == 1000


def test_put_no_ignora_mes_final_si_falta_la_migracion(monkeypatch):
    cursor = CursorConfiguracion(
        columnas=set(tipos_pagos_controller._ADVANCED_COLUMNS) - {"mes_final"}
    )
    conexion = ConexionConfiguracion(cursor)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)

    with pytest.raises(
        tipos_pagos_controller.MigracionPendienteError,
        match="20260910_tipos_pagos_mes_final.sql",
    ):
        tipos_pagos_controller.actualizar_configuracion_tipo_pago(
            4,
            {"mes_final": 11},
        )

    assert not any(query.startswith("update") for query, _ in cursor.ejecutadas)
    assert conexion.rollbacks == 1
    assert conexion.commits == 0


@pytest.mark.parametrize(
    ("configuracion_guardada", "cambio"),
    [
        (("mensual", 10, 12), {"mes_final": 9}),
        (("mensual", 2, 11), {"mes_inicial": 12}),
        (("unico", 10, 9), {"tipo_cobro": "mensual"}),
    ],
)
def test_put_valida_la_combinacion_efectiva_con_el_valor_guardado(
    monkeypatch,
    configuracion_guardada,
    cambio,
):
    cursor = CursorConfiguracion(
        columnas=tipos_pagos_controller._ADVANCED_COLUMNS,
        configuracion=configuracion_guardada,
    )
    conexion = ConexionConfiguracion(cursor)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)

    with pytest.raises(
        tipos_pagos_controller.ConfiguracionTipoPagoInvalidaError,
        match="mes final no puede ser anterior",
    ):
        tipos_pagos_controller.actualizar_configuracion_tipo_pago(
            4,
            cambio,
        )

    consulta_rango = next(
        query for query, _ in cursor.ejecutadas if query.startswith("select tipo_cobro")
    )
    assert consulta_rango.endswith("for update")
    assert conexion.rollbacks == 1
    assert conexion.commits == 0


def test_put_guarda_un_mes_final_valido_y_confirma_la_transaccion(monkeypatch):
    cursor = CursorConfiguracion(
        columnas=tipos_pagos_controller._ADVANCED_COLUMNS,
        configuracion=("mensual", 2, 12),
    )
    conexion = ConexionConfiguracion(cursor)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)

    resultado = tipos_pagos_controller.actualizar_configuracion_tipo_pago(
        4,
        {"mes_final": 11},
    )

    actualizacion = next(
        (query, params)
        for query, params in cursor.ejecutadas
        if query.startswith("update tipos_de_pagos")
    )
    assert resultado is True
    assert "mes_final = %s" in actualizacion[0]
    assert actualizacion[1] == [11, 4]
    assert conexion.commits == 1
    assert conexion.rollbacks == 0


def test_put_no_exige_orden_de_meses_para_un_concepto_no_mensual(monkeypatch):
    cursor = CursorConfiguracion(
        columnas=tipos_pagos_controller._ADVANCED_COLUMNS,
        configuracion=("mensual", 10, 12),
    )
    conexion = ConexionConfiguracion(cursor)
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)

    resultado = tipos_pagos_controller.actualizar_configuracion_tipo_pago(
        4,
        {"tipo_cobro": "unico", "mes_final": 9},
    )

    assert resultado is True
    assert conexion.commits == 1
    assert conexion.rollbacks == 0


def test_ruta_traduce_rango_efectivo_invalido_a_400(monkeypatch):
    def rechazar(_id, _config):
        raise tipos_pagos_controller.ConfiguracionTipoPagoInvalidaError(
            "El mes final no puede ser anterior al mes inicial."
        )

    monkeypatch.setattr(
        rutas_tipos_pagos,
        "actualizar_configuracion_tipo_pago",
        rechazar,
    )

    with pytest.raises(rutas_tipos_pagos.HTTPException) as exc_info:
        rutas_tipos_pagos.update_configuracion_tipo_pago(
            4,
            rutas_tipos_pagos.ConfiguracionTipoPago(mes_final=9),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El mes final no puede ser anterior al mes inicial."


def test_migracion_y_esquema_base_conservan_default_y_restricciones():
    migracion = MIGRACION.read_text(encoding="utf-8").lower()
    base = ESQUEMA_BASE.read_text(encoding="utf-8").lower()

    assert "add column if not exists mes_final smallint" in migracion
    assert "set mes_final = 12" in migracion
    assert "alter column mes_final set default 12" in migracion
    assert "alter column mes_final set not null" in migracion
    assert "check (mes_final between 1 and 12)" in migracion
    assert "tipo_cobro <> 'mensual'" in migracion
    assert "or mes_inicial is null" in migracion
    assert "or mes_final >= mes_inicial" in migracion

    assert "20260910_tipos_pagos_mes_final.sql" in base
    assert "mes_final smallint default 12 not null" in base
    assert "constraint chk_mes_final" in base
    assert "constraint chk_rango_meses_recurrencia" in base
