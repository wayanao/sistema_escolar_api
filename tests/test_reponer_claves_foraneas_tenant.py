import re

from scripts import reponer_claves_foraneas_tenant as reponer


PLANTILLA = "tenant_colegio_1"
TENANT = "tenant_2005"


def normalizar(query):
    texto = str(query)
    if not texto.startswith(("Composed(", "SQL(", "Identifier(", "Literal(")):
        return texto
    partes = re.findall(r"'([^']*)'|Literal\((\d+)\)", texto)
    return "".join(a or b for a, b in partes)


def fk(tabla, columna, tabla_ref, columna_ref="id", nombre=None, extra=""):
    return (
        tabla,
        [columna],
        tabla_ref,
        [columna_ref],
        nombre or f"{tabla}_{columna}_fkey",
        f"FOREIGN KEY ({columna}) REFERENCES {tabla_ref}({columna_ref}){extra}",
    )


class FakeCursor:
    def __init__(self, plantilla=None, destino=None, huerfanos=None):
        self.plantilla = plantilla or []
        self.destino = destino or []
        self.huerfanos = huerfanos or {}
        self.calls = []
        self._resultado = []

    def execute(self, query, params=None):
        texto = normalizar(query)
        self.calls.append((texto, params))
        if "pg_constraint" in texto and "contype" in texto:
            schema = params[0]
            self._resultado = list(
                self.plantilla if schema == PLANTILLA else self.destino
            )
        elif "COUNT(*)" in texto:
            tabla = next((t for t in self.huerfanos if t in texto), None)
            self._resultado = [(self.huerfanos.get(tabla, 0),)]
        else:
            self._resultado = []

    def fetchall(self):
        return self._resultado

    def fetchone(self):
        return self._resultado[0] if self._resultado else None

    def ejecuto(self, fragmento):
        return any(fragmento in texto for texto, _ in self.calls)

    def cuenta(self, fragmento):
        return sum(1 for texto, _ in self.calls if fragmento in texto)


def test_detecta_la_clave_que_le_falta_al_destino():
    cursor = FakeCursor(
        plantilla=[fk("asistencia", "estudiante_id", "estudiantes"),
                   fk("pagos", "estudiante_id", "estudiantes")],
        destino=[fk("pagos", "estudiante_id", "estudiantes")],
    )

    ausentes = reponer.claves_ausentes(cursor, PLANTILLA, TENANT)

    assert [c["tabla"] for c in ausentes] == ["asistencia"]


def test_una_clave_presente_con_otro_nombre_no_se_duplica():
    """La identidad es tabla, columnas y tabla referenciada; el nombre no cuenta."""
    cursor = FakeCursor(
        plantilla=[fk("pagos", "estudiante_id", "estudiantes", nombre="a")],
        destino=[fk("pagos", "estudiante_id", "estudiantes", nombre="b")],
    )

    assert reponer.claves_ausentes(cursor, PLANTILLA, TENANT) == []


def test_la_definicion_conserva_on_delete_cascade():
    cursor = FakeCursor(
        plantilla=[fk("asistencia", "asignacion_id", "asignaciones",
                      extra=" ON DELETE CASCADE")],
        destino=[],
    )

    ausentes = reponer.claves_ausentes(cursor, PLANTILLA, TENANT)

    assert "ON DELETE CASCADE" in ausentes[0]["definicion"]


def test_crear_clave_usa_la_definicion_tal_cual():
    cursor = FakeCursor()
    clave = {
        "tabla": "asistencia", "columnas": ["asignacion_id"],
        "tabla_ref": "asignaciones", "columnas_ref": ["id"],
        "nombre": "asistencia_asignacion_id_fkey",
        "definicion": "FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE",
    }

    reponer.crear_clave(cursor, TENANT, clave)

    texto = cursor.calls[0][0]
    assert "ALTER TABLE" in texto
    assert "ADD CONSTRAINT" in texto
    assert "asistencia_asignacion_id_fkey" in texto
    assert "ON DELETE CASCADE" in texto


def test_cuenta_huerfanos_con_not_exists_e_ignora_los_nulos():
    cursor = FakeCursor(huerfanos={"asistencia": 7})
    clave = {
        "tabla": "asistencia", "columnas": ["estudiante_id"],
        "tabla_ref": "estudiantes", "columnas_ref": ["id"],
        "nombre": "x", "definicion": "",
    }

    assert reponer.contar_huerfanos(cursor, TENANT, clave) == 7
    texto = cursor.calls[0][0]
    assert "NOT EXISTS" in texto
    assert "IS NOT NULL" in texto


def test_una_clave_compuesta_no_se_comprueba_y_devuelve_none():
    cursor = FakeCursor()
    clave = {
        "tabla": "x", "columnas": ["a", "b"], "tabla_ref": "y",
        "columnas_ref": ["a", "b"], "nombre": "x", "definicion": "",
    }

    assert reponer.contar_huerfanos(cursor, TENANT, clave) is None


def test_la_identidad_distingue_tablas_referenciadas_distintas():
    izquierda = {"tabla": "pagos", "columnas": ["x"], "tabla_ref": "ventas"}
    derecha = {"tabla": "pagos", "columnas": ["x"], "tabla_ref": "estudiantes"}

    assert reponer.identidad(izquierda) != reponer.identidad(derecha)


def test_no_se_repone_sobre_la_propia_plantilla():
    assert reponer.main(PLANTILLA, PLANTILLA) == 1


def test_detecta_claves_que_apuntan_a_otro_schema():
    """Guarda contra el error real cometido al escribir este script.

    `pg_get_constraintdef` devuelve `REFERENCES cursos(id)` sin cualificar. Si el
    search_path apunta a la plantilla al crear la clave, la tabla padre se
    resuelve alli y queda un acoplamiento entre schemas. En el ensayo esto
    reventó con una ForeignKeyViolation; sin datos que lo delataran se habria
    creado en silencio.
    """
    cursor = FakeCursor()
    cursor._resultado = [("asignaciones", "asignaciones_curso_id_fkey", PLANTILLA)]

    class CursorFijo(FakeCursor):
        def execute(self, query, params=None):
            self.calls.append((normalizar(query), params))
            self._resultado = [
                ("asignaciones", "asignaciones_curso_id_fkey", PLANTILLA)
            ]

    fijo = CursorFijo()
    cruzadas = reponer.claves_que_apuntan_fuera(fijo, TENANT)

    assert cruzadas == [("asignaciones", "asignaciones_curso_id_fkey", PLANTILLA)]
    texto, params = fijo.calls[0]
    assert "nsp_ref.nspname <> %s" in texto
    assert params == (TENANT, TENANT)
