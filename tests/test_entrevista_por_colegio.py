"""La entrevista de admisión, solo en los colegios que la usan (2026-10-30).

Ver docs/funcionalidades/ENTREVISTA_ADMISION.md, "Solo en los colegios que
la usan". Las pruebas usan dobles: no tocan una base real ni aplican la
migración.
"""
import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException

from app import dependencies
from app.core import tenant_status
from app.globals import tenant_schema_var
from app.routes import tenant as rutas_tenant

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "migrations" / "public" / "20261030_colegios_entrevista_admision.sql"


class CursorFalso:
    def __init__(self, fila):
        self.fila = fila
        self.consultas = []
        self.cerrado = False

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.fila

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.cerrada = False
        self.tenant_al_abrir = None

    def cursor(self):
        return self._cursor

    def close(self):
        self.cerrada = True


def _conexion(monkeypatch, fila):
    cursor = CursorFalso(fila)
    conexion = ConexionFalsa(cursor)

    def abrir():
        conexion.tenant_al_abrir = tenant_schema_var.get()
        return conexion

    monkeypatch.setattr(tenant_status, "get_connection", abrir)
    return conexion, cursor


# ---------------------------------------------------------------------------
# La migración.
# ---------------------------------------------------------------------------


def test_la_migracion_es_publica_y_los_colegios_nuevos_empiezan_sin_entrevista():
    sql = " ".join(MIGRACION.read_text(encoding="utf-8").split())

    assert (
        "ALTER TABLE public.colegios ADD COLUMN IF NOT EXISTS "
        "usa_entrevista_admision BOOLEAN NOT NULL DEFAULT FALSE"
    ) in sql


def test_la_migracion_deja_la_entrevista_en_los_dos_colegios_que_ya_existen():
    """Demo y 2005 la usan hoy: para ellos no cambia nada."""
    sql = " ".join(MIGRACION.read_text(encoding="utf-8").split())

    assert (
        "UPDATE public.colegios SET usa_entrevista_admision = TRUE "
        "WHERE esquema_db IN ('tenant_2005', 'tenant_colegio_1')"
    ) in sql


# ---------------------------------------------------------------------------
# Leer el dato del colegio.
# ---------------------------------------------------------------------------


def test_lee_el_dato_en_public_por_el_esquema_y_restaura_el_tenant(monkeypatch):
    conexion, cursor = _conexion(monkeypatch, (True,))
    token = tenant_schema_var.set("tenant_2005")
    try:
        usa = tenant_status.colegio_usa_entrevista_admision("tenant_2005")
        despues = tenant_schema_var.get()
    finally:
        tenant_schema_var.reset(token)

    assert usa is True
    assert conexion.tenant_al_abrir == "public"
    assert despues == "tenant_2005"
    assert cursor.consultas == [
        (
            "SELECT usa_entrevista_admision FROM colegios WHERE esquema_db = %s",
            ("tenant_2005",),
        )
    ]
    assert cursor.cerrado and conexion.cerrada


@pytest.mark.parametrize("fila", [(False,), None])
def test_sin_la_marca_o_sin_el_colegio_no_usa_entrevista(monkeypatch, fila):
    _conexion(monkeypatch, fila)

    assert tenant_status.colegio_usa_entrevista_admision("tenant_nuevo") is False


# ---------------------------------------------------------------------------
# GET /tenant/status lo cuenta al frontend.
# ---------------------------------------------------------------------------


def test_el_estado_del_colegio_dice_si_usa_entrevista(monkeypatch):
    monkeypatch.setattr(
        rutas_tenant, "get_tenant_by_schema", lambda esquema: {"estado": "activo"}
    )
    pedidos = []

    def usa(esquema):
        pedidos.append(esquema)
        return True

    monkeypatch.setattr(rutas_tenant, "colegio_usa_entrevista_admision", usa)

    respuesta = rutas_tenant.tenant_status({"id": 1, "rol": "admin", "tenant": "tenant_2005"})

    assert respuesta == {
        "estado": "activo",
        "mostrar_aviso": False,
        "mensaje": "",
        "usa_entrevista_admision": True,
    }
    assert pedidos == ["tenant_2005"]


# ---------------------------------------------------------------------------
# Las dependencias que usan las rutas.
# ---------------------------------------------------------------------------


def test_la_dependencia_pregunta_por_el_colegio_de_quien_llama(monkeypatch):
    pedidos = []

    def usa(esquema):
        pedidos.append(esquema)
        return False

    monkeypatch.setattr(dependencies, "colegio_usa_entrevista_admision", usa)

    usa_entrevista = asyncio.run(
        dependencies.usa_entrevista_admision({"id": 1, "rol": "admin", "tenant": "tenant_x"})
    )

    assert usa_entrevista is False
    assert pedidos == ["tenant_x"]


def test_exigir_la_entrevista_rechaza_con_403_si_el_colegio_no_la_usa():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(dependencies.exigir_entrevista_admision(False))

    assert exc.value.status_code == 403
    assert exc.value.detail == "Este colegio no usa la entrevista de admisión."


def test_exigir_la_entrevista_deja_pasar_si_el_colegio_la_usa():
    assert asyncio.run(dependencies.exigir_entrevista_admision(True)) is None


def test_la_dependencia_es_solo_para_admin():
    """Así un profesor recibe 403 antes de que se consulte nada."""
    import inspect

    parametro = inspect.signature(dependencies.usa_entrevista_admision).parameters[
        "current_user"
    ]

    assert parametro.default.dependency is dependencies.get_current_active_admin
