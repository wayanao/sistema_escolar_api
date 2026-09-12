from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.controllers import plan_de_clases_controller
from app.repositories import plan_de_clases_repository
from app.schemas.plan_de_clases import PlanDeClasesCreate
from scripts import auditar_plan_de_clases_integridad


class FakeCursor:
    def __init__(self, returned_id=91, returned_version=1, returned_state="pendiente"):
        self.calls = []
        self.returned_id = returned_id
        self.returned_version = returned_version
        self.returned_state = returned_state

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return (self.returned_id, self.returned_version, self.returned_state)


class AuditCursor:
    def __init__(self, results):
        self.calls = []
        self.results = iter(results)

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return next(self.results)

    def fetchall(self):
        return []


def crear_plan(version_esperada=None):
    return PlanDeClasesCreate(
        asignacion_id=15,
        version_esperada=version_esperada,
        periodo=2,
        unidad="Fracciones",
        proposito="Resolver situaciones",
        clase="Apertura, desarrollo y cierre",
        estandar="Pensamiento numerico",
        dba="Compara fracciones",
        competencias="Trabajo en parejas",
        actividad_casa="Ejercicios de refuerzo",
        tema="Fracciones equivalentes",
        fecha=date(2026, 7, 22),
    )


def test_guardar_plan_usa_un_solo_upsert_atomico(monkeypatch):
    cursor = FakeCursor(returned_id=127, returned_version=3)

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 44,
    )

    resultado = plan_de_clases_repository.guardar_plan_de_clases(crear_plan())

    assert resultado == {
        "id": 127,
        "version_revision": 3,
        "estado_revision": "pendiente",
    }
    assert len(cursor.calls) == 2
    query, params = cursor.calls[0]
    assert "INSERT INTO plan_de_clases" in query
    assert "ON CONFLICT (asignacion_id, fecha)" in query
    assert "DO UPDATE SET" in query
    assert "version_revision = plan_de_clases.version_revision + 1" in query
    assert "plan_de_clases.estado_revision IN ('revisado', 'con_observaciones')" in query
    assert "RETURNING id, version_revision, estado_revision" in query
    assert params[0] == 44
    assert params[10] == date(2026, 7, 22)
    notification_query, notification_params = cursor.calls[1]
    assert "INSERT INTO plan_de_clases_notificaciones_admin" in notification_query
    assert notification_params == (127, 3)


def test_guardar_plan_valida_la_version_esperada_dentro_de_la_transaccion(monkeypatch):
    cursor = AuditCursor(
        [
            (2,),
            (127, 3, "pendiente"),
        ]
    )

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 44,
    )

    resultado = plan_de_clases_repository.guardar_plan_de_clases(
        crear_plan(version_esperada=2)
    )

    assert resultado == {
        "id": 127,
        "version_revision": 3,
        "estado_revision": "pendiente",
    }
    assert "FOR UPDATE" in cursor.calls[0][0]
    assert cursor.calls[0][1] == (44, date(2026, 7, 22))
    assert "COALESCE(plan_de_clases.version_revision, 1) = %s" in cursor.calls[1][0]
    assert cursor.calls[1][1][-2:] == (2, 2)


def test_guardar_plan_rechaza_una_version_desactualizada_sin_escribir(monkeypatch):
    cursor = AuditCursor([(3,)])

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 44,
    )

    resultado = plan_de_clases_repository.guardar_plan_de_clases(
        crear_plan(version_esperada=2)
    )

    assert resultado == {
        "resultado": "version_desactualizada",
        "version_actual": 3,
    }
    assert len(cursor.calls) == 1
    assert "INSERT INTO plan_de_clases" not in cursor.calls[0][0]


def test_guardar_plan_nuevo_detecta_creacion_concurrente(monkeypatch):
    cursor = AuditCursor(
        [
            None,
            None,
            (1,),
        ]
    )

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 44,
    )

    resultado = plan_de_clases_repository.guardar_plan_de_clases(
        crear_plan(version_esperada=0)
    )

    assert resultado == {
        "resultado": "version_desactualizada",
        "version_actual": 1,
    }
    assert len(cursor.calls) == 3
    assert "WHERE %s IS NULL" in cursor.calls[1][0]
    assert cursor.calls[1][1][-2:] == (0, 0)


def test_controlador_limpia_imagenes_nuevas_si_hay_conflicto(monkeypatch):
    paths = iter(["/uploads/tenant/imagen-1.jpg", "/uploads/tenant/imagen-2.jpg"])
    eliminadas = []

    monkeypatch.setattr(
        plan_de_clases_controller,
        "obtener_directorio_archivos",
        lambda: "tenant/plan_de_clases",
    )
    monkeypatch.setattr(
        plan_de_clases_controller,
        "guardar_imagen_plan",
        lambda _directorio, _imagen: next(paths),
    )
    monkeypatch.setattr(
        plan_de_clases_controller,
        "guardar_plan",
        lambda *_args: {
            "resultado": "version_desactualizada",
            "version_actual": 4,
        },
    )
    monkeypatch.setattr(
        plan_de_clases_controller,
        "delete_file",
        eliminadas.append,
    )

    with pytest.raises(HTTPException) as exc:
        plan_de_clases_controller.crear_plan_de_clases_controller(
            crear_plan(version_esperada=3),
            imagen1=object(),
            imagen2=object(),
        )

    assert exc.value.status_code == 409
    assert exc.value.detail["version_actual"] == 4
    assert eliminadas == [
        "/uploads/tenant/imagen-1.jpg",
        "/uploads/tenant/imagen-2.jpg",
    ]


def test_correccion_con_observaciones_no_reabre_revision_admin(monkeypatch):
    cursor = FakeCursor(
        returned_id=127,
        returned_version=4,
        returned_state="con_observaciones",
    )

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 44,
    )

    resultado = plan_de_clases_repository.guardar_plan_de_clases(crear_plan())

    assert resultado == {
        "id": 127,
        "version_revision": 4,
        "estado_revision": "con_observaciones",
    }
    assert len(cursor.calls) == 1
    query, _params = cursor.calls[0]
    assert "THEN plan_de_clases.estado_revision" in query
    assert "RETURNING id, version_revision, estado_revision" in query


def test_plan_revisado_no_reabre_revision_admin(monkeypatch):
    cursor = FakeCursor(
        returned_id=127,
        returned_version=5,
        returned_state="revisado",
    )

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 44,
    )

    resultado = plan_de_clases_repository.guardar_plan_de_clases(crear_plan())

    assert resultado == {
        "id": 127,
        "version_revision": 5,
        "estado_revision": "revisado",
    }
    assert len(cursor.calls) == 1
    query, _params = cursor.calls[0]
    assert "plan_de_clases.estado_revision IN ('revisado', 'con_observaciones')" in query
    assert "THEN plan_de_clases.estado_revision" in query


def test_eliminar_evidencia_de_correccion_no_notifica_de_nuevo(monkeypatch):
    cursor = AuditCursor(
        [
            ("evidencias/plan-127.jpg", "con_observaciones"),
            (5, "con_observaciones"),
        ]
    )

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)

    ruta = plan_de_clases_repository.eliminar_imagen_plan(
        127,
        "imagen1",
        reiniciar_revision=True,
    )

    assert ruta == "evidencias/plan-127.jpg"
    assert len(cursor.calls) == 2
    assert "FOR UPDATE" in cursor.calls[0][0]
    assert "RETURNING version_revision, estado_revision" in cursor.calls[1][0]


def test_eliminar_evidencia_revisada_no_notifica_de_nuevo(monkeypatch):
    cursor = AuditCursor(
        [
            ("evidencias/plan-127.jpg", "revisado"),
            (6, "revisado"),
        ]
    )

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)

    ruta = plan_de_clases_repository.eliminar_imagen_plan(
        127,
        "imagen1",
        reiniciar_revision=True,
    )

    assert ruta == "evidencias/plan-127.jpg"
    assert len(cursor.calls) == 2
    query, _params = cursor.calls[1]
    assert "plan_de_clases.estado_revision IN ('revisado', 'con_observaciones')" in query
    assert "THEN estado_revision" in query


def test_filtros_admin_separan_pendientes_de_vistos(monkeypatch):
    cursores = []

    @contextmanager
    def fake_get_cursor(commit=False):
        cursor = AuditCursor([(0,)])
        cursores.append(cursor)
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)

    plan_de_clases_repository.listar_planes_admin(estado_revision="pendiente")
    plan_de_clases_repository.listar_planes_admin(estado_revision="revisado")
    plan_de_clases_repository.listar_planes_admin(estado_revision="visto")

    consultas_pendientes = " ".join(query for query, _params in cursores[0].calls)
    consultas_revisadas = " ".join(query for query, _params in cursores[1].calls)
    consultas_vistas = " ".join(query for query, _params in cursores[2].calls)
    # Pendiente es su propio cajon: marcar como visto saca el plan de la cola.
    assert "estado_revision = 'pendiente'" in consultas_pendientes
    assert "IN ('pendiente', 'visto')" not in consultas_pendientes
    assert "IN ('revisado', 'con_observaciones')" in consultas_revisadas
    assert "pdc.estado_revision = %s" in consultas_vistas


def test_historial_asignacion_aplica_paginacion_opcional(monkeypatch):
    cursor = AuditCursor([])

    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is False
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 44,
    )

    resultado = plan_de_clases_repository.obtener_planes_por_asignacion(
        15,
        limit=4,
        offset=6,
    )

    assert resultado == []
    query, params = cursor.calls[0]
    assert "LIMIT %s OFFSET %s" in query
    assert params == (44, 4, 6)

    plan_de_clases_repository.obtener_planes_por_asignacion(15)
    query_sin_limite, params_sin_limite = cursor.calls[1]
    assert "LIMIT %s OFFSET %s" not in query_sin_limite
    assert params_sin_limite == (44,)


def test_upsert_conserva_imagenes_si_no_se_envian_archivos_nuevos(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def fake_get_cursor(commit=False):
        yield cursor

    monkeypatch.setattr(plan_de_clases_repository, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        plan_de_clases_repository,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: asignacion_id,
    )

    plan_de_clases_repository.guardar_plan_de_clases(crear_plan())

    query, params = cursor.calls[0]
    assert "COALESCE(EXCLUDED.imagen1, plan_de_clases.imagen1)" in query
    assert "COALESCE(EXCLUDED.imagen2, plan_de_clases.imagen2)" in query
    assert params[11:13] == (None, None)


def test_migracion_rechaza_duplicados_antes_de_crear_indice_unico():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "20260722_plan_de_clases_integridad.sql"
    )
    sql = migration_path.read_text(encoding="utf-8")

    duplicate_guard_position = sql.index("HAVING COUNT(*) > 1")
    unique_index_position = sql.index("CREATE UNIQUE INDEX")

    assert duplicate_guard_position < unique_index_position
    assert "RAISE EXCEPTION" in sql
    assert "ALTER COLUMN asignacion_id SET NOT NULL" in sql
    assert "ALTER COLUMN fecha SET NOT NULL" in sql
    assert "uq_plan_de_clases_asignacion_fecha" in sql


def test_auditoria_reporta_invalidos_y_grupos_duplicados():
    cursor = AuditCursor([(3,), (2,)])

    resultado = auditar_plan_de_clases_integridad.audit_schema(cursor, "tenant_demo")

    assert resultado == {"invalidos": 3, "grupos_duplicados": 2}
    assert len(cursor.calls) == 2
    assert all(params is None for _, params in cursor.calls)
