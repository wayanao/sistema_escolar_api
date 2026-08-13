import apply_migration
from scripts import auditar_migraciones_tenants as auditoria


SQL_UNO = "ALTER TABLE demo ADD COLUMN uno BOOLEAN;"
SQL_DOS = "ALTER TABLE demo ADD COLUMN dos BOOLEAN;"

CHECKSUM_UNO = apply_migration.calculate_checksum(SQL_UNO)
CHECKSUM_DOS = apply_migration.calculate_checksum(SQL_DOS)

ESPERADAS = {"001_uno.sql": CHECKSUM_UNO, "002_dos.sql": CHECKSUM_DOS}


class FakeCursor:
    def __init__(self, rows=None, one=None):
        self.rows = rows or []
        self.one = one
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((str(query), params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.one


def test_el_checksum_es_el_mismo_que_usa_el_runner():
    # Si esta igualdad se rompe, la auditoria reportaria divergencias falsas.
    assert auditoria.calculate_checksum is apply_migration.calculate_checksum


def test_cargar_migraciones_lee_los_sql_directos_y_su_checksum(tmp_path):
    (tmp_path / "001_uno.sql").write_text(SQL_UNO, encoding="utf-8")
    (tmp_path / "002_dos.sql").write_text(SQL_DOS, encoding="utf-8")
    (tmp_path / "README.md").write_text("no es una migracion", encoding="utf-8")

    assert auditoria.cargar_migraciones(tmp_path) == ESPERADAS


def test_cargar_migraciones_no_desciende_al_subdirectorio_public(tmp_path):
    (tmp_path / "001_uno.sql").write_text(SQL_UNO, encoding="utf-8")
    publico = tmp_path / "public"
    publico.mkdir()
    (publico / "900_publica.sql").write_text(SQL_DOS, encoding="utf-8")

    assert list(auditoria.cargar_migraciones(tmp_path)) == ["001_uno.sql"]
    assert list(auditoria.cargar_migraciones(publico)) == ["900_publica.sql"]


def test_cargar_migraciones_devuelve_vacio_si_no_existe_el_directorio(tmp_path):
    assert auditoria.cargar_migraciones(tmp_path / "no_existe") == {}


def test_revisar_destino_detecta_lo_que_falta_y_lo_que_diverge():
    aplicadas = {"001_uno.sql": CHECKSUM_UNO}

    faltantes, divergentes = auditoria.revisar_destino(ESPERADAS, aplicadas)

    assert faltantes == ["002_dos.sql"]
    assert divergentes == []


def test_revisar_destino_marca_un_checksum_distinto_como_divergente():
    aplicadas = {"001_uno.sql": "otro-checksum", "002_dos.sql": CHECKSUM_DOS}

    faltantes, divergentes = auditoria.revisar_destino(ESPERADAS, aplicadas)

    assert faltantes == []
    assert divergentes == ["001_uno.sql"]


def test_fetch_tenants_no_filtra_por_estado():
    cursor = FakeCursor(rows=[("tenant_a", "A", "suspendido")])

    resultado = auditoria.fetch_tenants(cursor)

    assert resultado == [("tenant_a", "A", "suspendido")]
    consulta = cursor.calls[0][0]
    assert "FROM public.colegios" in consulta
    # Sin WHERE no hay filtro posible: es lo que distingue esta consulta de la
    # del runner, que solo alcanza 'activo' y 'en_mora'.
    assert "WHERE" not in consulta
    assert "LOWER(estado)" not in consulta


def test_historial_existe_es_de_solo_lectura():
    presente = FakeCursor(one=("public.schema_migrations",))
    ausente = FakeCursor(one=(None,))

    assert auditoria.historial_existe(presente) is True
    assert auditoria.historial_existe(ausente) is False
    assert "to_regclass" in presente.calls[0][0]
    assert "CREATE" not in presente.calls[0][0]


def test_agrupar_por_schema_indexa_por_destino_y_nombre():
    filas = [
        ("001_uno.sql", "tenant_a", CHECKSUM_UNO),
        ("001_uno.sql", "tenant_b", CHECKSUM_UNO),
        ("002_dos.sql", "tenant_a", CHECKSUM_DOS),
    ]

    assert auditoria.agrupar_por_schema(filas) == {
        "tenant_a": {"001_uno.sql": CHECKSUM_UNO, "002_dos.sql": CHECKSUM_DOS},
        "tenant_b": {"001_uno.sql": CHECKSUM_UNO},
    }


def test_un_tenant_suspendido_atrasado_se_marca_como_omitido_por_el_runner():
    tenants = [("tenant_suspendido", "Colegio Pausado", "suspendido")]
    aplicadas = {"tenant_suspendido": {"001_uno.sql": CHECKSUM_UNO}}

    informe = auditoria.construir_informe(ESPERADAS, {}, tenants, aplicadas)
    entrada = informe[1]

    assert entrada["omitido_por_el_runner"] is True
    assert entrada["faltantes"] == ["002_dos.sql"]
    assert auditoria.omitidos_y_atrasados(informe) == [entrada]


def test_un_tenant_cancelado_tambien_queda_fuera_del_alcance_del_runner():
    tenants = [("tenant_cerrado", "Colegio Cerrado", "CANCELADO")]

    informe = auditoria.construir_informe(ESPERADAS, {}, tenants, {})

    assert informe[1]["estado"] == "cancelado"
    assert informe[1]["omitido_por_el_runner"] is True


def test_un_tenant_activo_atrasado_no_se_marca_como_omitido():
    tenants = [("tenant_a", "Colegio A", "activo")]

    informe = auditoria.construir_informe(ESPERADAS, {}, tenants, {})

    assert informe[1]["omitido_por_el_runner"] is False
    assert auditoria.omitidos_y_atrasados(informe) == []
    assert auditoria.destinos_con_pendientes(informe) == [informe[1]]


def test_un_tenant_recien_creado_aparece_sin_ninguna_migracion_registrada():
    # Es el defecto que 3.0 encontro en el alta: schema copiado, historial vacio.
    tenants = [("tenant_nuevo", "Colegio Nuevo", "activo")]

    informe = auditoria.construir_informe(ESPERADAS, {}, tenants, {})

    assert informe[1]["faltantes"] == ["001_uno.sql", "002_dos.sql"]


def test_un_tenant_al_dia_no_aparece_como_pendiente():
    tenants = [("tenant_a", "Colegio A", "activo")]
    aplicadas = {"tenant_a": dict(ESPERADAS)}

    informe = auditoria.construir_informe(ESPERADAS, {}, tenants, aplicadas)

    assert auditoria.destinos_con_pendientes(informe) == []


def test_el_informe_incluye_siempre_el_destino_publico():
    esperadas_public = {"900_publica.sql": CHECKSUM_DOS}

    informe = auditoria.construir_informe({}, esperadas_public, [], {})

    assert informe[0]["schema"] == "public"
    assert informe[0]["omitido_por_el_runner"] is False
    assert informe[0]["faltantes"] == ["900_publica.sql"]


def test_el_formato_distingue_al_dia_pendiente_y_omitido():
    tenants = [
        ("tenant_a", "Colegio A", "activo"),
        ("tenant_b", "Colegio B", "suspendido"),
    ]
    aplicadas = {"tenant_a": dict(ESPERADAS)}

    lineas = auditoria.formatear_informe(
        auditoria.construir_informe(ESPERADAS, {}, tenants, aplicadas)
    )
    texto = "\n".join(lineas)

    assert "OK        tenant_a (Colegio A, activo)" in texto
    assert "PENDIENTE tenant_b (Colegio B, suspendido) [el runner lo omite]" in texto
    assert "falta      001_uno.sql" in texto
    assert "falta      002_dos.sql" in texto
