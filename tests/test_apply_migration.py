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

    def __init__(self, lock_granted=True, tenants=None, applied_checksum=None):
        self.calls = []
        self.closed = False
        self._lock_granted = lock_granted
        self._tenants = [("tenant_a", "Colegio A")] if tenants is None else tenants
        self._applied_checksum = applied_checksum
        self._next_fetchone = None

    def execute(self, query, params=None):
        text = str(query)
        self.calls.append((text, params))
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


def run_runner(monkeypatch, tmp_path, cursor, dry_run=False, sql_text=SQL_DEMO):
    sql_path = tmp_path / "20260813_demo.sql"
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
