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
