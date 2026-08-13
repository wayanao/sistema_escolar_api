"""Caracterizacion del alta de tenant, previa a rehacerla desde migraciones.

Estas pruebas fijan lo que el alta hace **hoy**, incluido un defecto conocido:
no siembra `public.schema_migrations`. Ver
`test_el_alta_todavia_no_siembra_el_historial_de_migraciones`.
"""
import psycopg2
import pytest
from fastapi import HTTPException

from app.config import settings
from app.controllers import super_admin_controller
from app.globals import tenant_schema_var


PAYLOAD_VALIDO = {
    "nombre": "Colegio Nuevo",
    "codigo": "nuevo",
    "admin_nombre": "Admin Nuevo",
    "admin_email": "ADMIN@COLEGIO.COM",
    "admin_password": "Temporal123",
    "fecha_inicio": "2026-06-01",
    "fecha_proximo_pago": "2026-07-01",
    "dias_gracia": 5,
    "notas": "Plan mensual",
}

COLEGIO_ROW = (9, "Colegio Nuevo", "nuevo", "tenant_nuevo", "activo")


class ProvisioningCursor:
    """Cursor que guarda el SQL como texto para poder inspeccionar `sql.Composed`."""

    def __init__(self, rows=None, fail_on=None, error=None):
        self.rows = list(rows or [])
        self.calls = []
        self.closed = False
        self._fail_on = fail_on
        self._error = error or RuntimeError("fallo simulado")

    def execute(self, query, params=None):
        text = str(query)
        self.calls.append((text, params))
        if self._fail_on and self._fail_on in text:
            raise self._error

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        return list(self.rows)

    def close(self):
        self.closed = True

    def executed(self, fragment):
        return any(fragment in text for text, _ in self.calls)

    def index_of(self, fragment):
        for position, (text, _) in enumerate(self.calls):
            if fragment in text:
                return position
        return -1


class ProvisioningConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def crear_tenant(monkeypatch, cursor, payload=None, super_admin_id=7):
    conn = ProvisioningConnection(cursor)
    monkeypatch.setattr(super_admin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(super_admin_controller, "get_password_hash", lambda password: f"hash:{password}")

    resultado = super_admin_controller.crear_tenant_controller(
        dict(payload or PAYLOAD_VALIDO), super_admin_id=super_admin_id
    )
    return resultado, conn


def test_el_alta_crea_el_schema_derivado_del_codigo(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    resultado, conn = crear_tenant(monkeypatch, cursor)

    assert cursor.executed("CREATE SCHEMA")
    assert cursor.executed("tenant_nuevo")
    assert resultado["esquema_db"] == "tenant_nuevo"
    assert conn.committed is True


def test_el_alta_copia_la_estructura_del_schema_plantilla(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    assert cursor.executed("pg_tables")
    assert cursor.executed("INCLUDING ALL")
    assert cursor.executed(settings.DEFAULT_TENANT_SCHEMA)


def test_el_alta_todavia_no_siembra_el_historial_de_migraciones(monkeypatch):
    """Fija el defecto que 3.3 debe corregir.

    Un tenant recien creado nace con la estructura actual de la plantilla pero
    con historial vacio, asi que el runner lo vera como si le faltaran todas las
    migraciones. Cuando 3.3 siembre `public.schema_migrations` en el alta, esta
    prueba **debe fallar**: ese fallo es la senal de que el defecto quedo
    corregido y hay que reemplazarla por su version positiva.
    """
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    # Control positivo: el inspector si encuentra lo que el alta realmente hace,
    # asi que la ausencia de historial no puede deberse a un fragmento mal
    # escrito ni a un cursor que no registro nada.
    assert cursor.executed("INSERT INTO public.colegios")
    assert not cursor.executed("schema_migrations")


def test_el_alta_copia_solo_las_plantillas_predefinidas(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    assert cursor.executed("INSERT INTO plantilla_impresion")
    assert cursor.executed("es_predefinida = TRUE")


def test_el_alta_registra_el_colegio_antes_de_crear_el_schema(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    assert cursor.index_of("INSERT INTO public.colegios") < cursor.index_of("CREATE SCHEMA")
    assert cursor.index_of("CREATE SCHEMA") < cursor.index_of("pg_tables")


def test_el_alta_nace_en_estado_activo(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    resultado, _ = crear_tenant(monkeypatch, cursor)

    assert cursor.executed("'activo'")
    assert resultado["estado"] == "activo"


def test_el_alta_crea_el_admin_inicial_obligado_a_cambiar_password(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    assert cursor.executed("INSERT INTO usuarios")
    assert cursor.executed("debe_cambiar_password")
    assert ("Admin Nuevo", "admin@colegio.com", "hash:Temporal123") in [
        params for _, params in cursor.calls
    ]


def test_el_alta_revierte_y_cierra_si_falla_la_copia_de_estructura(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW], fail_on="pg_tables")

    with pytest.raises(RuntimeError):
        crear_tenant(monkeypatch, cursor)

    assert cursor.closed is True


def test_un_codigo_o_correo_duplicado_se_traduce_a_409(monkeypatch):
    cursor = ProvisioningCursor(
        rows=[COLEGIO_ROW],
        fail_on="INSERT INTO public.colegios",
        error=psycopg2.IntegrityError("duplicado"),
    )

    with pytest.raises(HTTPException) as exc:
        crear_tenant(monkeypatch, cursor)

    assert exc.value.status_code == 409
    assert cursor.closed is True


def test_el_alta_restaura_el_contexto_de_tenant_al_terminar(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])
    previo = tenant_schema_var.get()

    crear_tenant(monkeypatch, cursor)

    assert tenant_schema_var.get() == previo


def test_el_alta_restaura_el_contexto_de_tenant_aunque_falle(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW], fail_on="CREATE SCHEMA")
    previo = tenant_schema_var.get()

    with pytest.raises(RuntimeError):
        crear_tenant(monkeypatch, cursor)

    assert tenant_schema_var.get() == previo
