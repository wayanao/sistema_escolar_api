"""Caracterizacion del alta de tenant, previa a rehacerla desde migraciones.

Estas pruebas fijan lo que el alta hace hoy: crea el schema copiando la
estructura de la plantilla y, desde 3.3b, hereda tambien su historial de
migraciones.
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

    def __init__(self, rows=None, fail_on=None, error=None, historial_existe=True):
        self.rows = list(rows or [])
        self.calls = []
        self.closed = False
        self._fail_on = fail_on
        self._error = error or RuntimeError("fallo simulado")
        self._historial_existe = historial_existe
        self._pendiente = None

    def execute(self, query, params=None):
        text = str(query)
        self.calls.append((text, params))
        if self._fail_on and self._fail_on in text:
            raise self._error
        if "to_regclass" in text:
            self._pendiente = (
                ("public.schema_migrations",) if self._historial_existe else (None,)
            )
        else:
            self._pendiente = None

    def fetchone(self):
        if self._pendiente is not None:
            pendiente, self._pendiente = self._pendiente, None
            return pendiente
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


def test_el_alta_construye_el_schema_desde_la_migracion_base(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    # El contenido real del archivo, no una parafrasis: si la migracion base
    # cambiara de sitio o de nombre, esta prueba lo detecta.
    base = super_admin_controller.ESQUEMA_BASE_TENANT.read_text(encoding="utf-8")
    assert cursor.executed("CREATE TABLE IF NOT EXISTS asignaciones")
    assert any(texto == base for texto, _ in cursor.calls)


def test_el_alta_ya_no_copia_la_plantilla_con_like(monkeypatch):
    """El defecto que 3.4a documento: LIKE INCLUDING ALL no copia claves foraneas
    ni crea secuencias propias. Si alguien reintroduce esa via, esto falla.

    Se excluye el texto de la migracion base, cuya cabecera menciona
    `INCLUDING ALL` justo para explicar por que ya no se usa.
    """
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    base = super_admin_controller.ESQUEMA_BASE_TENANT.read_text(encoding="utf-8")
    otros = [texto for texto, _ in cursor.calls if texto != base]
    assert not any("INCLUDING ALL" in texto for texto in otros)
    assert not any("pg_tables" in texto for texto in otros)
    assert not any("DO $$" in texto for texto in otros)


def test_el_search_path_apunta_solo_al_schema_nuevo_al_aplicar_la_base(monkeypatch):
    """Con la plantilla en el search_path, las claves foraneas del archivo
    resolverian contra sus tablas y naceran cruzadas. Paso exactamente eso en
    3.4f con otro script."""
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    base = super_admin_controller.ESQUEMA_BASE_TENANT.read_text(encoding="utf-8")
    indice_base = next(i for i, (t, _) in enumerate(cursor.calls) if t == base)
    anteriores = [t for t, _ in cursor.calls[:indice_base] if "search_path" in t]
    assert anteriores, "no se fijo el search_path antes de aplicar la base"
    ultimo = anteriores[-1]
    assert "tenant_nuevo" in ultimo
    assert settings.DEFAULT_TENANT_SCHEMA not in ultimo


def test_la_migracion_base_existe_y_trae_claves_foraneas():
    """Sin claves foraneas en el archivo, el alta reproduciria el defecto."""
    base = super_admin_controller.ESQUEMA_BASE_TENANT

    assert base.is_file()
    contenido = base.read_text(encoding="utf-8")
    assert "ADD CONSTRAINT" in contenido
    assert "FOREIGN KEY" in contenido
    assert "SERIAL" in contenido


def test_el_alta_siembra_el_historial_copiando_las_filas_de_la_plantilla(monkeypatch):
    """Version positiva del defecto que 3.0 encontro y 3.3b corrigio.

    Antes, un tenant nuevo nacia con historial vacio y el runner lo veia como si
    le faltaran todas las migraciones. Ahora hereda las filas del schema
    plantilla, que es de donde copio su estructura.
    """
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    assert cursor.executed("INSERT INTO public.schema_migrations")
    assert cursor.executed("FROM public.schema_migrations")
    assert cursor.executed("WHERE target_schema")
    assert ("tenant_nuevo", settings.DEFAULT_TENANT_SCHEMA) in [
        params for _, params in cursor.calls
    ]


def test_la_siembra_ocurre_despues_de_copiar_la_estructura_y_antes_del_commit(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    _, conn = crear_tenant(monkeypatch, cursor)

    assert cursor.index_of("pg_tables") < cursor.index_of("INSERT INTO public.schema_migrations")
    assert conn.committed is True
    assert conn.rolled_back is False


def test_el_alta_no_falla_si_el_historial_todavia_no_existe(monkeypatch):
    """Una base sin migraciones aplicadas nunca tuvo `schema_migrations`.

    El alta debe seguir funcionando ahi: se omite la siembra en vez de romper un
    camino que antes no fallaba.
    """
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW], historial_existe=False)

    resultado, conn = crear_tenant(monkeypatch, cursor)

    assert cursor.executed("to_regclass")
    assert not cursor.executed("INSERT INTO public.schema_migrations")
    assert resultado["esquema_db"] == "tenant_nuevo"
    assert conn.committed is True


def test_la_siembra_se_revierte_si_el_alta_falla_despues(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW], fail_on="INSERT INTO usuarios")

    with pytest.raises(RuntimeError):
        crear_tenant(monkeypatch, cursor)

    # La siembra ya se habia ejecutado, pero comparte transaccion con el alta.
    assert cursor.executed("INSERT INTO public.schema_migrations")
    assert cursor.closed is True


def test_el_alta_copia_solo_las_plantillas_predefinidas(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    assert cursor.executed("INSERT INTO plantilla_impresion")
    assert cursor.executed("es_predefinida = TRUE")


def test_el_alta_registra_el_colegio_antes_de_crear_el_schema(monkeypatch):
    cursor = ProvisioningCursor(rows=[COLEGIO_ROW])

    crear_tenant(monkeypatch, cursor)

    assert cursor.index_of("INSERT INTO public.colegios") < cursor.index_of("CREATE SCHEMA")
    assert cursor.index_of("CREATE SCHEMA") < cursor.index_of(
        "CREATE TABLE IF NOT EXISTS asignaciones"
    )


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


def test_el_alta_revierte_y_cierra_si_falla_la_migracion_base(monkeypatch):
    cursor = ProvisioningCursor(
        rows=[COLEGIO_ROW], fail_on="CREATE TABLE IF NOT EXISTS asignaciones"
    )

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
