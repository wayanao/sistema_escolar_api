import apply_migration


class FakeCursor:
    def __init__(self):
        self.calls = []
        self.fetchone_result = None
        self.fetchall_result = []

    def execute(self, query, params=None):
        self.calls.append((str(query), params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


def test_calculate_checksum_is_stable():
    sql_text = "ALTER TABLE ejemplo ADD COLUMN activo BOOLEAN;"

    assert apply_migration.calculate_checksum(sql_text) == apply_migration.calculate_checksum(sql_text)
    assert apply_migration.calculate_checksum(sql_text) != apply_migration.calculate_checksum(sql_text + "\n")


def test_ensure_migration_history_creates_public_table():
    cursor = FakeCursor()

    apply_migration.ensure_migration_history(cursor)

    assert "CREATE TABLE IF NOT EXISTS public.schema_migrations" in cursor.calls[0][0]


def test_get_migration_record_filters_by_name_and_schema():
    cursor = FakeCursor()
    cursor.fetchone_result = ("abc123",)

    result = apply_migration.get_migration_record(cursor, "001.sql", "tenant_demo")

    assert result == ("abc123",)
    assert cursor.calls[0][1] == ("001.sql", "tenant_demo")


def test_record_migration_stores_name_schema_and_checksum():
    cursor = FakeCursor()

    apply_migration.record_migration(cursor, "001.sql", "tenant_demo", "abc123")

    assert "INSERT INTO public.schema_migrations" in cursor.calls[0][0]
    assert cursor.calls[0][1] == ("001.sql", "tenant_demo", "abc123")


def test_fetch_active_tenants_only_operational_ordered():
    cursor = FakeCursor()
    cursor.fetchall_result = [("tenant_demo", "Colegio Demo")]

    result = apply_migration.fetch_active_tenants(cursor)

    assert result == [("tenant_demo", "Colegio Demo")]
    assert "WHERE LOWER(estado) IN ('activo', 'en_mora')" in cursor.calls[0][0]


def test_is_public_migration_detects_public_folder():
    assert apply_migration.is_public_migration(apply_migration.Path("migrations/public/001.sql")) is True
    assert apply_migration.is_public_migration(apply_migration.Path("migrations/001.sql")) is False


def test_try_acquire_migration_lock_uses_the_fixed_key():
    cursor = FakeCursor()
    cursor.fetchone_result = (True,)

    assert apply_migration.try_acquire_migration_lock(cursor) is True
    assert "pg_try_advisory_lock" in cursor.calls[0][0]
    assert cursor.calls[0][1] == (apply_migration.MIGRATION_LOCK_KEY,)


def test_try_acquire_migration_lock_returns_false_when_another_run_holds_it():
    cursor = FakeCursor()
    cursor.fetchone_result = (False,)

    assert apply_migration.try_acquire_migration_lock(cursor) is False


def test_try_acquire_migration_lock_treats_missing_row_as_not_acquired():
    cursor = FakeCursor()
    cursor.fetchone_result = None

    assert apply_migration.try_acquire_migration_lock(cursor) is False


SQL_DEMO = "ALTER TABLE demo ADD COLUMN activo BOOLEAN;"


class ScriptedCursor:
    """Cursor que responde segun el SQL recibido, para recorrer el runner entero."""

    def __init__(
        self,
        lock_granted=True,
        tenants=None,
        applied_checksum=None,
        fail_on_schemas=(),
        migration_sql=SQL_DEMO,
    ):
        self.calls = []
        self.closed = False
        self.current_schema = None
        self._lock_granted = lock_granted
        self._tenants = [("tenant_a", "Colegio A")] if tenants is None else tenants
        self._applied_checksum = applied_checksum
        self._fail_on_schemas = set(fail_on_schemas)
        self._migration_sql = migration_sql
        self._next_fetchone = None

    def execute(self, query, params=None):
        text = str(query)
        self.calls.append((text, params))

        if "search_path" in text:
            self.current_schema = next(
                (schema for schema, _ in self._tenants if schema in text), "public"
            )
        if text == self._migration_sql and self.current_schema in self._fail_on_schemas:
            raise RuntimeError(f"fallo simulado en {self.current_schema}")

        if "pg_try_advisory_lock" in text:
            self._next_fetchone = (self._lock_granted,)
        elif "FROM public.schema_migrations" in text:
            self._next_fetchone = (self._applied_checksum,) if self._applied_checksum else None
        else:
            self._next_fetchone = None

    def fetchone(self):
        return self._next_fetchone

    def fetchall(self):
        return list(self._tenants)

    def close(self):
        self.closed = True

    def executed(self, fragment):
        return any(fragment in text for text, _ in self.calls)

    def count(self, fragment):
        return sum(1 for text, _ in self.calls if fragment in text)

    def params_for(self, fragment):
        return [params for text, params in self.calls if fragment in text]


class RunnerConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False
        self.autocommit = None

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def run_runner(monkeypatch, tmp_path, cursor, dry_run=False, sql_text=SQL_DEMO, public=False):
    directory = tmp_path / "public" if public else tmp_path
    directory.mkdir(exist_ok=True)
    sql_path = directory / "20260813_demo.sql"
    sql_path.write_text(sql_text, encoding="utf-8")
    conn = RunnerConnection(cursor)

    monkeypatch.setattr(apply_migration, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    monkeypatch.setattr(apply_migration.psycopg2, "connect", lambda url: conn)

    exit_code = apply_migration.apply_migration(sql_path, dry_run=dry_run)
    return exit_code, conn


def test_runner_applies_and_records_when_the_lock_is_free(monkeypatch, tmp_path):
    cursor = ScriptedCursor()

    exit_code, conn = run_runner(monkeypatch, tmp_path, cursor)

    assert exit_code == 0
    assert cursor.executed("CREATE TABLE IF NOT EXISTS public.schema_migrations")
    assert cursor.executed("FROM public.colegios")
    assert cursor.executed("search_path")
    assert cursor.executed(SQL_DEMO)
    assert cursor.executed("INSERT INTO public.schema_migrations")
    assert conn.commits >= 2
    assert conn.closed is True


def test_runner_takes_the_lock_before_touching_the_history():
    cursor = ScriptedCursor()

    apply_migration.try_acquire_migration_lock(cursor)

    assert "pg_try_advisory_lock" in cursor.calls[0][0]


def test_runner_refuses_to_run_while_another_execution_holds_the_lock(monkeypatch, tmp_path):
    cursor = ScriptedCursor(lock_granted=False)

    exit_code, conn = run_runner(monkeypatch, tmp_path, cursor)

    assert exit_code == 2
    assert len(cursor.calls) == 1
    assert "pg_try_advisory_lock" in cursor.calls[0][0]
    assert not cursor.executed("CREATE TABLE IF NOT EXISTS public.schema_migrations")
    assert not cursor.executed("FROM public.colegios")
    assert not cursor.executed(SQL_DEMO)
    assert not cursor.executed("INSERT INTO public.schema_migrations")
    assert conn.commits == 0
    assert cursor.closed is True
    assert conn.closed is True


def test_lock_is_requested_before_any_history_or_tenant_query(monkeypatch, tmp_path):
    cursor = ScriptedCursor()

    run_runner(monkeypatch, tmp_path, cursor)

    assert "pg_try_advisory_lock" in cursor.calls[0][0]
    assert cursor.calls[0][1] == (apply_migration.MIGRATION_LOCK_KEY,)


def test_runner_skips_an_already_applied_migration_without_reapplying(monkeypatch, tmp_path):
    cursor = ScriptedCursor(applied_checksum=apply_migration.calculate_checksum(SQL_DEMO))

    exit_code, _ = run_runner(monkeypatch, tmp_path, cursor)

    assert exit_code == 0
    assert not cursor.executed(SQL_DEMO)
    assert not cursor.executed("INSERT INTO public.schema_migrations")


def test_runner_blocks_a_same_name_migration_with_a_different_checksum(monkeypatch, tmp_path):
    cursor = ScriptedCursor(applied_checksum="otro-checksum")

    exit_code, _ = run_runner(monkeypatch, tmp_path, cursor)

    assert exit_code == 2
    assert not cursor.executed(SQL_DEMO)
    assert not cursor.executed("INSERT INTO public.schema_migrations")


def test_dry_run_still_takes_the_lock_but_applies_nothing(monkeypatch, tmp_path):
    cursor = ScriptedCursor()

    exit_code, _ = run_runner(monkeypatch, tmp_path, cursor, dry_run=True)

    assert exit_code == 0
    assert "pg_try_advisory_lock" in cursor.calls[0][0]
    assert not cursor.executed(SQL_DEMO)
    assert not cursor.executed("INSERT INTO public.schema_migrations")


def test_runner_reports_nothing_to_do_when_there_are_no_operational_tenants(monkeypatch, tmp_path):
    cursor = ScriptedCursor(tenants=[])

    exit_code, conn = run_runner(monkeypatch, tmp_path, cursor)

    assert exit_code == 0
    assert not cursor.executed(SQL_DEMO)
    assert conn.closed is True


TRES_TENANTS = [("tenant_a", "Colegio A"), ("tenant_b", "Colegio B"), ("tenant_c", "Colegio C")]


def test_a_failing_tenant_does_not_stop_the_following_ones(monkeypatch, tmp_path):
    cursor = ScriptedCursor(tenants=TRES_TENANTS, fail_on_schemas={"tenant_b"})

    exit_code, conn = run_runner(monkeypatch, tmp_path, cursor)

    # Se intento en los tres, pero solo dos quedaron registrados: el fallo de
    # tenant_b revierte su transaccion y no interrumpe a tenant_c.
    assert cursor.count(SQL_DEMO) == 3
    assert cursor.count("INSERT INTO public.schema_migrations") == 2
    assert exit_code == 2
    assert conn.rollbacks >= 1
    assert conn.closed is True


def test_the_failing_tenant_is_the_only_one_missing_from_the_history(monkeypatch, tmp_path):
    cursor = ScriptedCursor(tenants=TRES_TENANTS, fail_on_schemas={"tenant_b"})

    run_runner(monkeypatch, tmp_path, cursor)

    registrados = [
        params[1] for params in cursor.params_for("INSERT INTO public.schema_migrations")
    ]
    assert registrados == ["tenant_a", "tenant_c"]


def test_a_failure_in_the_first_tenant_still_processes_the_rest(monkeypatch, tmp_path):
    cursor = ScriptedCursor(tenants=TRES_TENANTS, fail_on_schemas={"tenant_a"})

    exit_code, _ = run_runner(monkeypatch, tmp_path, cursor)

    registrados = [
        params[1] for params in cursor.params_for("INSERT INTO public.schema_migrations")
    ]
    assert registrados == ["tenant_b", "tenant_c"]
    assert exit_code == 2


def test_dry_run_over_several_tenants_applies_and_records_nothing(monkeypatch, tmp_path):
    cursor = ScriptedCursor(tenants=TRES_TENANTS)

    exit_code, conn = run_runner(monkeypatch, tmp_path, cursor, dry_run=True)

    assert exit_code == 0
    assert cursor.count(SQL_DEMO) == 0
    assert cursor.count("INSERT INTO public.schema_migrations") == 0
    assert not cursor.executed("search_path")
    assert conn.closed is True


def test_public_migration_targets_only_public_and_records_it(monkeypatch, tmp_path):
    cursor = ScriptedCursor()

    exit_code, conn = run_runner(monkeypatch, tmp_path, cursor, public=True)

    assert exit_code == 0
    assert cursor.executed("SET search_path TO public")
    assert cursor.executed(SQL_DEMO)
    assert not cursor.executed("FROM public.colegios")
    assert cursor.params_for("INSERT INTO public.schema_migrations") == [
        ("20260813_demo.sql", "public", apply_migration.calculate_checksum(SQL_DEMO))
    ]
    assert conn.closed is True


def test_public_migration_also_takes_the_lock_first(monkeypatch, tmp_path):
    cursor = ScriptedCursor()

    run_runner(monkeypatch, tmp_path, cursor, public=True)

    assert "pg_try_advisory_lock" in cursor.calls[0][0]


def test_public_migration_refuses_to_run_without_the_lock(monkeypatch, tmp_path):
    cursor = ScriptedCursor(lock_granted=False)

    exit_code, _ = run_runner(monkeypatch, tmp_path, cursor, public=True)

    assert exit_code == 2
    assert len(cursor.calls) == 1
    assert not cursor.executed(SQL_DEMO)


def test_public_migration_already_applied_is_skipped(monkeypatch, tmp_path):
    cursor = ScriptedCursor(applied_checksum=apply_migration.calculate_checksum(SQL_DEMO))

    exit_code, _ = run_runner(monkeypatch, tmp_path, cursor, public=True)

    assert exit_code == 0
    assert not cursor.executed(SQL_DEMO)
    assert not cursor.executed("INSERT INTO public.schema_migrations")


def test_public_migration_with_a_different_checksum_is_blocked(monkeypatch, tmp_path):
    cursor = ScriptedCursor(applied_checksum="otro-checksum")

    exit_code, conn = run_runner(monkeypatch, tmp_path, cursor, public=True)

    assert exit_code == 2
    assert not cursor.executed(SQL_DEMO)
    assert conn.rollbacks >= 1


def test_public_dry_run_applies_nothing(monkeypatch, tmp_path):
    cursor = ScriptedCursor()

    exit_code, _ = run_runner(monkeypatch, tmp_path, cursor, public=True, dry_run=True)

    assert exit_code == 0
    assert not cursor.executed(SQL_DEMO)
    assert not cursor.executed("INSERT INTO public.schema_migrations")


def test_el_endpoint_agrupado_se_detecta_por_el_host():
    directo = "postgresql://u:p@ep-algo-1234.c-4.us-east-1.aws.neon.tech/db?sslmode=require"
    agrupado = "postgresql://u:p@ep-algo-1234-pooler.c-4.us-east-1.aws.neon.tech/db?sslmode=require"

    assert apply_migration.es_endpoint_agrupado(directo) is False
    assert apply_migration.es_endpoint_agrupado(agrupado) is True


def test_el_endpoint_agrupado_no_se_confunde_con_la_base_ni_los_parametros():
    # '-pooler' fuera del host no debe disparar la guarda.
    dsn = "postgresql://u:p@ep-algo.neon.tech/mi-pooler-db?options=-pooler"

    assert apply_migration.es_endpoint_agrupado(dsn) is False


def test_el_runner_se_niega_a_correr_sobre_el_endpoint_agrupado(monkeypatch, tmp_path):
    """El lock de sesion no se sostiene sobre PgBouncer: mejor negarse que fingir."""
    sql_path = tmp_path / "20260813_demo.sql"
    sql_path.write_text(SQL_DEMO, encoding="utf-8")

    def no_debe_conectar(url):
        raise AssertionError("no debio intentar conectar")

    monkeypatch.setattr(apply_migration, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://u:p@ep-algo-pooler.c-4.us-east-1.aws.neon.tech/db",
    )
    monkeypatch.setattr(apply_migration.psycopg2, "connect", no_debe_conectar)

    assert apply_migration.apply_migration(sql_path) == 1


def test_el_runner_si_corre_sobre_el_endpoint_directo(monkeypatch, tmp_path):
    cursor = ScriptedCursor()
    conn = RunnerConnection(cursor)

    sql_path = tmp_path / "20260813_demo.sql"
    sql_path.write_text(SQL_DEMO, encoding="utf-8")
    monkeypatch.setattr(apply_migration, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://u:p@ep-algo.c-4.us-east-1.aws.neon.tech/db"
    )
    monkeypatch.setattr(apply_migration.psycopg2, "connect", lambda url: conn)

    assert apply_migration.apply_migration(sql_path) == 0
    assert cursor.executed(SQL_DEMO)


def test_missing_file_and_missing_database_url_return_one(monkeypatch, tmp_path):
    assert apply_migration.apply_migration(tmp_path / "no_existe.sql") == 1

    sql_path = tmp_path / "20260813_demo.sql"
    sql_path.write_text(SQL_DEMO, encoding="utf-8")
    monkeypatch.setattr(apply_migration, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert apply_migration.apply_migration(sql_path) == 1
