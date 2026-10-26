"""Registrar el pago de un colegio: `POST /super-admin/tenants/{id}/pagos`.

El estado efectivo de un colegio sale de su fecha de proximo pago: vencida la
fecha y los dias de gracia, queda suspendido aunque su estado manual sea
`activo`. Hasta el 2026-10-26, reactivar a un colegio que pago exigia editar la
base a mano. El montaje HTTP de la ruta (200, 401 y 422) vive con el de las
demas en `test_super_admin_caracterizacion.py`.

Las fechas son relativas a hoy: el estado efectivo se calcula con el reloj real.
"""

from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.controllers import super_admin_controller
from app.core.tenant_status import calculate_effective_tenant_status
from app.globals import tenant_schema_var

HOY = date.today()
INICIO = HOY - timedelta(days=400)
VENCIDA = HOY - timedelta(days=60)
NUEVA = HOY + timedelta(days=30)


def _tenant(fecha_proximo_pago=VENCIDA, *, fecha_inicio=INICIO, estado="activo"):
    return (1, "Colegio Demo", "demo", "tenant_demo", estado, fecha_inicio, fecha_proximo_pago, 5)


class CursorFalso:
    def __init__(self, filas):
        self.filas = list(filas)
        self.llamadas = []
        self.cerrado = 0

    def execute(self, query, params=None):
        self.llamadas.append((" ".join(str(query).split()), params))

    def fetchone(self):
        return self.filas.pop(0) if self.filas else None

    def close(self):
        self.cerrado += 1


class ConexionFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada += 1


@pytest.fixture
def base_falsa(monkeypatch):
    """Una conexion falsa que devuelve las filas dadas, con "hoy" fijo en HOY."""
    monkeypatch.setattr(super_admin_controller, "hoy_en_colombia", lambda: HOY)

    def instalar(*filas):
        cursor = CursorFalso(filas)
        conexion = ConexionFalsa(cursor)
        contextos = []

        def get_connection():
            contextos.append(tenant_schema_var.get())
            return conexion

        monkeypatch.setattr(super_admin_controller, "get_connection", get_connection)
        return cursor, conexion, contextos

    return instalar


def test_sin_mover_la_fecha_activar_a_mano_no_reactiva():
    """El defecto que motiva la ruta: el estado manual no le gana a la fecha."""
    assert calculate_effective_tenant_status("activo", VENCIDA, 5) == "suspendido"


def test_registrar_pago_mueve_la_fecha_reactiva_y_audita(base_falsa):
    cursor, conexion, contextos = base_falsa(_tenant())

    externo = tenant_schema_var.set("tenant_externo")
    try:
        resultado = super_admin_controller.registrar_pago_tenant_controller(
            1,
            NUEVA.isoformat(),
            7,
            "  Pagó por transferencia  ",
        )
        contexto_despues = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(externo)

    assert resultado == {
        "id": 1,
        "nombre": "Colegio Demo",
        "subdominio": "demo",
        "esquema_db": "tenant_demo",
        "estado": "activo",
        "estado_manual": "activo",
        "fecha_inicio": INICIO.isoformat(),
        "fecha_proximo_pago": NUEVA.isoformat(),
        "dias_gracia": 5,
    }
    consultas = [consulta for consulta, _ in cursor.llamadas]
    assert len(consultas) == 3
    assert "FROM public.colegios" in consultas[0]
    assert consultas[1].startswith("UPDATE public.tenant_suscripciones")
    assert consultas[2].startswith("INSERT INTO public.tenant_eventos_auditoria")
    assert cursor.llamadas[1][1] == (NUEVA, 1)
    assert cursor.llamadas[2][1] == (
        1,
        "pago_registrado",
        f"Proximo pago: {VENCIDA.isoformat()} -> {NUEVA.isoformat()}. Nota: Pagó por transferencia",
        7,
    )
    assert (conexion.commits, conexion.rollbacks) == (1, 0)
    assert (cursor.cerrado, conexion.cerrada) == (1, 1)
    assert contextos == ["public"]
    assert contexto_despues == "tenant_externo"


def test_sin_nota_el_registro_solo_lleva_las_fechas(base_falsa):
    cursor, _, _ = base_falsa(_tenant())

    super_admin_controller.registrar_pago_tenant_controller(1, NUEVA.isoformat(), 7, "   ")

    assert cursor.llamadas[2][1][2] == f"Proximo pago: {VENCIDA.isoformat()} -> {NUEVA.isoformat()}"


def test_la_misma_fecha_no_deja_otro_registro(base_falsa):
    cursor, conexion, _ = base_falsa(_tenant(NUEVA))

    resultado = super_admin_controller.registrar_pago_tenant_controller(1, NUEVA.isoformat(), 7)

    assert resultado["estado"] == "activo"
    assert len(cursor.llamadas) == 1
    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert (cursor.cerrado, conexion.cerrada) == (1, 1)


@pytest.mark.parametrize(
    ("filas", "codigo", "detalle"),
    [
        ((), 404, "Tenant no encontrado"),
        (
            ((1, "Colegio Viejo", "viejo", "tenant_viejo", "activo", None, None, None),),
            422,
            "El colegio no tiene suscripcion registrada",
        ),
        (
            (_tenant(fecha_inicio=HOY + timedelta(days=60)),),
            422,
            "La proxima fecha de pago no puede ser anterior al inicio",
        ),
    ],
)
def test_lo_que_no_se_puede_pagar_no_cambia_nada(base_falsa, filas, codigo, detalle):
    cursor, conexion, _ = base_falsa(*filas)

    with pytest.raises(HTTPException) as error:
        super_admin_controller.registrar_pago_tenant_controller(1, NUEVA.isoformat(), 7)

    assert (error.value.status_code, error.value.detail) == (codigo, detalle)
    assert len(cursor.llamadas) == 1
    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert (cursor.cerrado, conexion.cerrada) == (1, 1)


@pytest.mark.parametrize(
    ("fecha", "detalle"),
    [
        ("no-es-fecha", "Fecha de proximo pago invalida"),
        (None, "Fecha de proximo pago invalida"),
        (HOY.isoformat(), "La proxima fecha de pago debe ser posterior a hoy"),
        ((HOY - timedelta(days=1)).isoformat(), "La proxima fecha de pago debe ser posterior a hoy"),
    ],
)
def test_una_fecha_invalida_o_que_no_reactiva_se_rechaza_sin_tocar_la_base(base_falsa, fecha, detalle):
    """Con una fecha de hoy o anterior, el colegio seguiria bloqueado."""
    _, _, contextos = base_falsa(_tenant())

    with pytest.raises(HTTPException) as error:
        super_admin_controller.registrar_pago_tenant_controller(1, fecha, 7)

    assert (error.value.status_code, error.value.detail) == (422, detalle)
    assert contextos == []


def test_un_fallo_al_guardar_revierte_todo(base_falsa):
    cursor, conexion, _ = base_falsa(_tenant())

    def fallar_al_auditar(query, params=None):
        cursor.llamadas.append((" ".join(str(query).split()), params))
        if len(cursor.llamadas) == 3:
            raise RuntimeError("fallo simulado")

    cursor.execute = fallar_al_auditar

    with pytest.raises(RuntimeError):
        super_admin_controller.registrar_pago_tenant_controller(1, NUEVA.isoformat(), 7)

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert (cursor.cerrado, conexion.cerrada) == (1, 1)
