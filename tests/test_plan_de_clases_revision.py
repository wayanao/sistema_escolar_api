from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.controllers import plan_de_clases_controller
from app.repositories import plan_de_clases_repository
from app.schemas.plan_de_clases import PlanObservacionCreate, PlanRevisionUpdate
from scripts import auditar_plan_de_clases_revision


class ScriptedCursor:
    def __init__(self, rows=None, all_rows=None):
        self.calls = []
        self.rows = iter(rows or [])
        self.all_rows = all_rows or []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return next(self.rows)

    def fetchall(self):
        return self.all_rows


class AuditCursor:
    def __init__(self, columns):
        self.calls = []
        self.columns = columns
        self.single_rows = iter([(1,), (1,), (0,)])

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchall(self):
        return [(column,) for column in self.columns]

    def fetchone(self):
        return next(self.single_rows)


def fake_cursor_context(cursor):
    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is True
        yield cursor

    return fake_get_cursor


def fake_read_cursor_context(cursor):
    @contextmanager
    def fake_get_cursor(commit=False):
        assert commit is False
        yield cursor

    return fake_get_cursor


def test_marcar_plan_visto_bloquea_y_valida_version(monkeypatch):
    visto_at = datetime(2026, 7, 22, 15, 30, tzinfo=timezone.utc)
    cursor = ScriptedCursor(rows=[(4,), ("visto", 4, visto_at, None)])
    monkeypatch.setattr(
        plan_de_clases_repository,
        "get_cursor",
        fake_cursor_context(cursor),
    )

    resultado = plan_de_clases_repository.actualizar_estado_revision_plan(
        plan_id=21,
        estado="visto",
        admin_id=8,
        version=4,
    )

    assert resultado["resultado"] == "ok"
    assert resultado["estado_revision"] == "visto"
    assert resultado["version_revision"] == 4
    assert "FOR UPDATE" in cursor.calls[0][0]
    assert cursor.calls[1][1] == (8, 21)
    # Marcar como visto tambien apaga la campanita del admin para ese plan.
    consulta_notificaciones = cursor.calls[2][0]
    assert "plan_de_clases_notificaciones_admin" in consulta_notificaciones
    assert "SET leida_at = COALESCE(leida_at, CURRENT_TIMESTAMP)" in consulta_notificaciones
    assert cursor.calls[2][1] == (21, 4)


def test_revision_rechaza_version_desactualizada_sin_actualizar(monkeypatch):
    cursor = ScriptedCursor(rows=[(5,)])
    monkeypatch.setattr(
        plan_de_clases_repository,
        "get_cursor",
        fake_cursor_context(cursor),
    )

    resultado = plan_de_clases_repository.actualizar_estado_revision_plan(
        plan_id=21,
        estado="revisado",
        admin_id=8,
        version=4,
    )

    assert resultado == {"resultado": "version_desactualizada", "version_actual": 5}
    assert len(cursor.calls) == 1


def test_revision_con_comentario_guarda_mensaje_y_aprobacion_juntos(monkeypatch):
    creada_at = datetime(2026, 7, 22, 15, 45, tzinfo=timezone.utc)
    revisado_at = datetime(2026, 7, 22, 15, 46, tzinfo=timezone.utc)
    cursor = ScriptedCursor(
        rows=[
            (4,),
            (92, 21, 8, 4, "Muy bien.", creada_at, None),
            ("revisado", 4, creada_at, revisado_at),
        ]
    )
    monkeypatch.setattr(
        plan_de_clases_repository,
        "get_cursor",
        fake_cursor_context(cursor),
    )

    resultado = plan_de_clases_repository.actualizar_estado_revision_plan(
        plan_id=21,
        estado="revisado",
        admin_id=8,
        version=4,
        comentario="Muy bien.",
    )

    assert resultado["estado_revision"] == "revisado"
    assert resultado["observacion"]["observacion"] == "Muy bien."
    assert resultado["observacion"]["plan_version"] == 4
    assert "INSERT INTO plan_de_clases_observaciones" in cursor.calls[1][0]
    assert "estado_revision = 'revisado'" in cursor.calls[2][0]
    assert "plan_de_clases_notificaciones_admin" in cursor.calls[3][0]


def test_observacion_queda_ligada_a_version_y_actualiza_estado(monkeypatch):
    creada_at = datetime(2026, 7, 22, 16, 0, tzinfo=timezone.utc)
    cursor = ScriptedCursor(
        rows=[
            (3,),
            (91, 21, 8, 3, "Reforzar el cierre.", creada_at, None),
        ]
    )
    monkeypatch.setattr(
        plan_de_clases_repository,
        "get_cursor",
        fake_cursor_context(cursor),
    )

    resultado = plan_de_clases_repository.agregar_observacion_plan(
        plan_id=21,
        admin_id=8,
        version=3,
        observacion="Reforzar el cierre.",
    )

    assert resultado["resultado"] == "ok"
    assert resultado["estado_revision"] == "con_observaciones"
    assert resultado["observacion"]["plan_version"] == 3
    assert cursor.calls[1][1] == (21, 8, 3, "Reforzar el cierre.")
    assert "estado_revision = 'con_observaciones'" in cursor.calls[2][0]


def test_controlador_convierte_conflicto_de_version_en_http_409(monkeypatch):
    monkeypatch.setattr(
        plan_de_clases_controller,
        "actualizar_revision",
        lambda *_args, **_kwargs: {
            "resultado": "version_desactualizada",
            "version_actual": 7,
        },
    )

    with pytest.raises(HTTPException) as exc:
        plan_de_clases_controller.actualizar_revision_plan_controller(
            21,
            type(
                "Revision",
                (),
                {"estado": "revisado", "version": 6, "comentario": None},
            )(),
            8,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail["version_actual"] == 7


def test_observacion_normaliza_espacios_y_rechaza_texto_vacio():
    data = PlanObservacionCreate(observacion="  Ajustar el propósito.  ", version=2)
    assert data.observacion == "Ajustar el propósito."

    with pytest.raises(ValidationError):
        PlanObservacionCreate(observacion="   ", version=2)


def test_comentario_de_aprobacion_es_opcional_y_se_normaliza():
    con_comentario = PlanRevisionUpdate(
        estado="revisado",
        version=2,
        comentario="  Muy buen trabajo.  ",
    )
    sin_comentario = PlanRevisionUpdate(
        estado="revisado",
        version=2,
        comentario="   ",
    )

    assert con_comentario.comentario == "Muy buen trabajo."
    assert sin_comentario.comentario is None

    with pytest.raises(ValidationError):
        PlanRevisionUpdate(
            estado="visto",
            version=2,
            comentario="No corresponde a una apertura.",
        )


def test_migracion_crea_flujo_versionado_sin_borrar_planes():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "20260722_plan_de_clases_revision.sql"
    )
    sql = migration_path.read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS estado_revision" in sql
    assert "ADD COLUMN IF NOT EXISTS version_revision" in sql
    assert "CREATE TABLE IF NOT EXISTS plan_de_clases_observaciones" in sql
    assert "ON DELETE CASCADE" in sql
    assert "DROP TABLE" not in sql.upper()
    assert "DELETE FROM plan_de_clases" not in sql


def test_auditoria_de_revision_confirma_estructura_completa():
    cursor = AuditCursor(auditar_plan_de_clases_revision.REQUIRED_COLUMNS)

    resultado = auditar_plan_de_clases_revision.audit_schema(cursor, "tenant_demo")

    assert resultado == {
        "missing_columns": [],
        "observations_table": True,
        "admin_notifications_table": True,
        "invalid_plans": 0,
    }
    assert len(cursor.calls) == 4


def test_notificaciones_admin_agrupa_eventos_no_leidos_por_profesor(monkeypatch):
    creada_at = datetime(2026, 7, 22, 18, 0, tzinfo=timezone.utc)
    cursor = ScriptedCursor(
        rows=[(3, 1)],
        all_rows=[
            (
                12,
                "Ana Docente",
                3,
                creada_at,
            )
        ],
    )
    monkeypatch.setattr(
        plan_de_clases_repository,
        "get_cursor",
        fake_read_cursor_context(cursor),
    )

    resultado = plan_de_clases_repository.listar_notificaciones_admin(limit=8)

    assert resultado["total_no_leidas"] == 3
    assert resultado["total_profesores"] == 1
    assert resultado["items"][0]["tipo"] == "planes_profesor"
    assert resultado["items"][0]["profesor_id"] == 12
    assert resultado["items"][0]["cantidad"] == 3
    assert "WHERE n.leida_at IS NULL" in cursor.calls[1][0]
    assert "GROUP BY a.profesor_id" in cursor.calls[1][0]


def test_notificaciones_profesor_solo_lista_observaciones_propias_no_leidas(monkeypatch):
    creada_at = datetime(2026, 7, 22, 18, 30, tzinfo=timezone.utc)
    cursor = ScriptedCursor(
        rows=[(2,)],
        all_rows=[
            (
                91,
                21,
                3,
                creada_at,
                "Reforzar el cierre de la clase.",
                55,
                datetime(2026, 7, 22).date(),
                "Fracciones",
                "Coordinacion",
                "Matematicas",
                "Quinto",
            )
        ],
    )
    monkeypatch.setattr(
        plan_de_clases_repository,
        "get_cursor",
        fake_read_cursor_context(cursor),
    )

    resultado = plan_de_clases_repository.listar_notificaciones_profesor(
        profesor_id=12,
        limit=8,
    )

    assert resultado["total_no_leidas"] == 2
    assert resultado["items"][0]["tipo"] == "observacion_plan"
    assert resultado["items"][0]["observacion"] == "Reforzar el cierre de la clase."
    assert cursor.calls[0][1] == (12,)
    assert cursor.calls[1][1] == (12, 8)
    assert "a.profesor_id = %s" in cursor.calls[1][0]
    assert "pco.vista_por_profesor_at IS NULL" in cursor.calls[1][0]


def test_migracion_notificaciones_no_genera_eventos_historicos():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "20260722_plan_de_clases_notificaciones.sql"
    )
    sql = migration_path.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS plan_de_clases_notificaciones_admin" in sql
    assert "UNIQUE (plan_id, plan_version)" in sql
    assert "INSERT INTO plan_de_clases_notificaciones_admin" not in sql
