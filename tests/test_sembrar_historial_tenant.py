import re

from scripts import sembrar_historial_tenant as sembrar


PLANTILLA = "tenant_colegio_1"
TENANT = "tenant_2005"


def normalizar(query):
    texto = str(query)
    if not texto.startswith(("Composed(", "SQL(", "Identifier(", "Literal(")):
        return texto
    partes = re.findall(r"'([^']*)'|Literal\((\d+)\)", texto)
    return "".join(a or b for a, b in partes)


class FakeCursor:
    def __init__(self, columnas=None, indices=None, pendientes=None, rowcount=0,
                 pendientes_tras_sembrar=None):
        self.columnas = columnas or {}
        self.indices = indices or {}
        self.pendientes = pendientes or []
        self.rowcount = rowcount
        self._pendientes_tras = (
            pendientes_tras_sembrar if pendientes_tras_sembrar is not None else []
        )
        self._ya_sembro = False
        self.calls = []
        self._resultado = []

    def execute(self, query, params=None):
        texto = normalizar(query)
        self.calls.append((texto, params))
        # psycopg2 devuelve tuplas; el doble hace lo mismo.
        if "information_schema.columns" in texto:
            schema = params[0]
            self._resultado = [
                (t, c, d, n) for (t, c), (d, n) in self.columnas.get(schema, {}).items()
            ]
        elif "pg_indexes" in texto:
            schema = params[0]
            self._resultado = [tuple(par) for par in self.indices.get(schema, set())]
        elif "INSERT INTO public.schema_migrations" in texto:
            self._ya_sembro = True
            self._resultado = []
        elif "FROM public.schema_migrations" in texto:
            fuente = self._pendientes_tras if self._ya_sembro else self.pendientes
            self._resultado = [tuple(par) for par in fuente]
        else:
            self._resultado = []

    def fetchall(self):
        return self._resultado

    def fetchone(self):
        return self._resultado[0] if self._resultado else None

    def ejecuto(self, fragmento):
        return any(fragmento in texto for texto, _ in self.calls)


IGUALES = {
    PLANTILLA: {("estudiantes", "id"): ("integer", "NO"),
                ("estudiantes", "estado"): ("character varying", "YES")},
    TENANT: {("estudiantes", "id"): ("integer", "NO"),
             ("estudiantes", "estado"): ("character varying", "YES")},
}
SIN_INDICES = {PLANTILLA: set(), TENANT: set()}


def test_detecta_las_migraciones_que_le_faltan_al_destino():
    cursor = FakeCursor(pendientes=[("001.sql", "abc"), ("002.sql", "def")])

    resultado = sembrar.migraciones_por_sembrar(cursor, PLANTILLA, TENANT)

    assert resultado == [("001.sql", "abc"), ("002.sql", "def")]
    assert cursor.calls[0][1] == (PLANTILLA, TENANT)


def test_sin_diferencias_estructurales_no_reporta_problemas():
    cursor = FakeCursor(columnas=IGUALES, indices=SIN_INDICES)

    assert sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT) == []


def test_una_columna_ausente_en_el_destino_es_un_problema():
    columnas = {
        PLANTILLA: dict(IGUALES[PLANTILLA]),
        TENANT: {("estudiantes", "id"): ("integer", "NO")},
    }
    cursor = FakeCursor(columnas=columnas, indices=SIN_INDICES)

    problemas = sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT)

    assert problemas == ["falta la columna estudiantes.estado"]


def test_una_columna_con_tipo_distinto_es_un_problema():
    columnas = {
        PLANTILLA: dict(IGUALES[PLANTILLA]),
        TENANT: {("estudiantes", "id"): ("integer", "NO"),
                 ("estudiantes", "estado"): ("text", "YES")},
    }
    cursor = FakeCursor(columnas=columnas, indices=SIN_INDICES)

    problemas = sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT)

    assert len(problemas) == 1
    assert "difiere" in problemas[0]


def test_un_indice_ausente_es_un_problema():
    indices = {
        PLANTILLA: {("estudiantes",
                     "CREATE INDEX idx_a ON estudiantes USING btree (curso_id)")},
        TENANT: set(),
    }
    cursor = FakeCursor(columnas=IGUALES, indices=indices)

    problemas = sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT)

    assert len(problemas) == 1
    assert problemas[0].startswith("falta un indice en estudiantes")


def test_el_mismo_indice_con_otro_nombre_no_es_un_problema():
    """La plantilla usa `idx_cursos_estado` y los tenants `cursos_estado_idx`.

    Es la misma funcion con distinta convencion de nombres. Comparar nombres
    daria 32 falsas diferencias sobre datos reales.
    """
    indices = {
        PLANTILLA: {("cursos",
                     "CREATE INDEX idx_cursos_estado ON cursos USING btree (estado)")},
        TENANT: {("cursos",
                  "CREATE INDEX cursos_estado_idx ON cursos USING btree (estado)")},
    }
    cursor = FakeCursor(columnas=IGUALES, indices=indices)

    assert sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT) == []


def test_un_indice_de_mas_en_el_destino_no_es_un_problema():
    indices = {
        PLANTILLA: set(),
        TENANT: {("cursos",
                  "CREATE INDEX extra ON cursos USING btree (nombre)")},
    }
    cursor = FakeCursor(columnas=IGUALES, indices=indices)

    assert sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT) == []


def test_la_unicidad_del_indice_si_cuenta():
    indices = {
        PLANTILLA: {("cursos",
                     "CREATE UNIQUE INDEX u ON cursos USING btree (codigo)")},
        TENANT: {("cursos", "CREATE INDEX n ON cursos USING btree (codigo)")},
    }
    cursor = FakeCursor(columnas=IGUALES, indices=indices)

    problemas = sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT)

    assert len(problemas) == 1
    assert "indice unico" in problemas[0]


def test_las_claves_foraneas_no_entran_en_la_comparacion():
    """Su ausencia viene de la copia con LIKE, no de una migracion sin aplicar."""
    cursor = FakeCursor(columnas=IGUALES, indices=SIN_INDICES)

    sembrar.diferencias_estructurales(cursor, PLANTILLA, TENANT)

    assert not cursor.ejecuto("pg_constraint")
    assert not cursor.ejecuto("contype")


def test_la_siembra_copia_los_registros_de_la_plantilla_sin_duplicar():
    cursor = FakeCursor(rowcount=15)

    insertadas = sembrar.sembrar(cursor, PLANTILLA, TENANT)

    assert insertadas == 15
    texto, params = cursor.calls[0]
    assert "INSERT INTO public.schema_migrations" in texto
    assert "NOT EXISTS" in texto
    assert params == (TENANT, PLANTILLA, TENANT)


def test_no_se_siembra_sobre_la_propia_plantilla():
    assert sembrar.main(PLANTILLA, PLANTILLA) == 1
