import re

from scripts import reparar_secuencias_tenant as reparar


PLANTILLA = "tenant_colegio_1"
TENANT = "tenant_2005"


def default_ajeno(tabla, columna="id"):
    return f"nextval('{PLANTILLA}.{tabla}_{columna}_seq'::regclass)"


def default_propio(tabla, columna="id"):
    return f"nextval('{TENANT}.{tabla}_{columna}_seq'::regclass)"


def normalizar(query):
    """`sql.Composed` se imprime como repr; se extrae su texto para inspeccionarlo.

    Los fragmentos con comillas se toman tal cual; `Literal(686)` es numerico y
    llega sin comillas, asi que se captura aparte.
    """
    texto = str(query)
    if not texto.startswith(("Composed(", "SQL(", "Identifier(", "Literal(")):
        return texto
    partes = re.findall(r"'([^']*)'|Literal\((\d+)\)", texto)
    return "".join(entrecomillado or numero for entrecomillado, numero in partes)


class FakeCursor:
    """Cursor guionizado: responde segun el SQL que recibe."""

    def __init__(self, columnas=None, maximos=None, secuencias=None):
        # columnas: lista de (tabla, columna, default, typname)
        # secuencias: {nombre_de_secuencia: (last_value, is_called)}
        self.columnas = columnas or []
        self.maximos = maximos or {}
        self.secuencias = secuencias or {}
        self.calls = []
        self._resultado = None

    def execute(self, query, params=None):
        texto = normalizar(query)
        self.calls.append((texto, params))

        if "pg_attrdef" in texto and "typname" in texto:
            self._resultado = [list(fila) for fila in self.columnas]
        elif "pg_attrdef" in texto:
            self._resultado = [
                [tabla, columna, expresion]
                for tabla, columna, expresion, _ in self.columnas
            ]
        elif "last_value" in texto:
            nombre = next((s for s in self.secuencias if s in texto), None)
            self._resultado = [list(self.secuencias.get(nombre, (1, False)))]
        elif "MAX(" in texto:
            tabla = next((t for t, _, _, _ in self.columnas if t in texto), None)
            self._resultado = [[self.maximos.get(tabla, 0)]]
        else:
            self._resultado = [[None]]

    def fetchone(self):
        return self._resultado[0] if self._resultado else None

    def fetchall(self):
        return self._resultado or []

    def ejecuto(self, fragmento):
        return any(fragmento in texto for texto, _ in self.calls)

    def cuenta(self, fragmento):
        return sum(1 for texto, _ in self.calls if fragmento in texto)


def test_detecta_solo_las_columnas_que_usan_secuencias_de_otro_schema():
    cursor = FakeCursor(
        columnas=[
            ("estudiantes", "id", default_ajeno("estudiantes"), "int4"),
            ("pagos_aplicaciones", "id", default_propio("pagos_aplicaciones"), "int8"),
            ("nombres", "nombre", "''::text", "text"),
        ]
    )

    prestadas = reparar.detectar_columnas_prestadas(cursor, TENANT)

    assert [p["tabla"] for p in prestadas] == ["estudiantes"]
    assert prestadas[0]["schema_origen"] == PLANTILLA
    assert prestadas[0]["tipo"] == "int4"


def test_no_confunde_una_secuencia_sin_schema_con_una_ajena():
    cursor = FakeCursor(
        columnas=[("cursos", "id", "nextval('cursos_id_seq'::regclass)", "int4")]
    )

    assert reparar.detectar_columnas_prestadas(cursor, TENANT) == []


def test_el_nombre_de_la_secuencia_propia_conserva_la_convencion():
    assert reparar.nombre_secuencia_propia("estudiantes", "id") == "estudiantes_id_seq"


def test_el_tipo_de_secuencia_sigue_al_de_la_columna():
    assert reparar.tipo_de_secuencia("int8") == "bigint"
    assert reparar.tipo_de_secuencia("int4") == "integer"


def test_el_plan_mide_el_maximo_en_el_momento_y_no_lo_lleva_precalculado():
    cursor = FakeCursor(
        columnas=[("estudiantes", "id", default_ajeno("estudiantes"), "int4")],
        maximos={"estudiantes": 685},
    )

    plan = reparar.construir_plan(cursor, TENANT)

    assert plan[0]["maximo"] == 685
    assert plan[0]["secuencia"] == "estudiantes_id_seq"
    assert cursor.ejecuto("MAX(")


def test_una_tabla_con_datos_deja_el_siguiente_id_por_encima_del_maximo():
    cursor = FakeCursor(columnas=[("estudiantes", "id", default_ajeno("estudiantes"), "int4")])
    paso = {
        "tabla": "estudiantes", "columna": "id", "tipo": "int4",
        "secuencia": "estudiantes_id_seq", "maximo": 685,
    }

    reparar.reparar_columna(cursor, TENANT, paso)

    assert cursor.ejecuto("CREATE SEQUENCE IF NOT EXISTS")
    assert cursor.ejecuto("RESTART WITH 686")
    assert cursor.ejecuto("SET DEFAULT nextval")
    assert cursor.ejecuto("OWNED BY")


def test_una_tabla_vacia_arranca_en_uno_sin_saltarselo():
    cursor = FakeCursor()
    paso = {
        "tabla": "egresos", "columna": "id", "tipo": "int4",
        "secuencia": "egresos_id_seq", "maximo": 0,
    }

    reparar.reparar_columna(cursor, TENANT, paso)

    assert cursor.ejecuto("RESTART WITH 1")


def test_no_se_usa_setval_porque_no_es_transaccional():
    """Guarda de regresion.

    setval() no se revierte con el rollback: comprobado contra PostgreSQL 17, su
    efecto persiste tras revertir la transaccion. Si alguien lo reintroduce, la
    reparacion dejaria de ser reversible aunque el resto siguiera pareciendolo.
    """
    cursor = FakeCursor()
    paso = {
        "tabla": "estudiantes", "columna": "id", "tipo": "int4",
        "secuencia": "estudiantes_id_seq", "maximo": 685,
    }

    reparar.reparar_columna(cursor, TENANT, paso)

    assert not cursor.ejecuto("setval")


def test_la_secuencia_nueva_hereda_bigint_cuando_la_columna_lo_es():
    cursor = FakeCursor()
    paso = {
        "tabla": "pagos_aplicaciones", "columna": "id", "tipo": "int8",
        "secuencia": "pagos_aplicaciones_id_seq", "maximo": 3,
    }

    reparar.reparar_columna(cursor, TENANT, paso)

    assert cursor.ejecuto("AS bigint")


def test_la_verificacion_denuncia_una_columna_que_sigue_prestada():
    cursor = FakeCursor(
        columnas=[("estudiantes", "id", default_ajeno("estudiantes"), "int4")],
        maximos={"estudiantes": 685},
        secuencias={"estudiantes_id_seq": (8, True)},
    )

    problemas = reparar.verificar(cursor, TENANT)

    assert any("sigue usando" in p for p in problemas)


def test_la_verificacion_denuncia_una_secuencia_por_debajo_del_maximo():
    cursor = FakeCursor(
        columnas=[("estudiantes", "id", default_propio("estudiantes"), "int4")],
        maximos={"estudiantes": 685},
        secuencias={"estudiantes_id_seq": (8, True)},
    )

    problemas = reparar.verificar(cursor, TENANT)

    assert problemas == ["estudiantes.id: siguiente id 9 <= maximo 685"]


def test_la_verificacion_acepta_una_secuencia_ya_posicionada():
    cursor = FakeCursor(
        columnas=[("estudiantes", "id", default_propio("estudiantes"), "int4")],
        maximos={"estudiantes": 685},
        secuencias={"estudiantes_id_seq": (685, True)},
    )

    assert reparar.verificar(cursor, TENANT) == []


def test_una_tabla_vacia_con_secuencia_en_uno_es_correcta():
    cursor = FakeCursor(
        columnas=[("egresos", "id", default_propio("egresos"), "int4")],
        maximos={"egresos": 0},
        secuencias={"egresos_id_seq": (1, False)},
    )

    assert reparar.verificar(cursor, TENANT) == []


def test_un_tenant_ya_reparado_no_genera_plan():
    cursor = FakeCursor(
        columnas=[("estudiantes", "id", default_propio("estudiantes"), "int4")]
    )

    assert reparar.construir_plan(cursor, TENANT) == []
