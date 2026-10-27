"""Fase 3 del observador unificado: crear y editar anotaciones.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Varias de estas pruebas
protegen invariantes que, si se rompen, **no fallan de forma visible**: la
anotacion se guarda igual, solo que firmada por quien no la escribio o sin
rastro de que alguien la cambio. Un observador que no se puede defender ante una
reclamacion no sirve para lo que existe.
"""
from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core import permissions
from app.routes import observador
from app.schemas.observador import AnotacionCreate, AnotacionUpdate


PROFESOR = {"id": 7, "rol": "profesor"}
OTRO_PROFESOR = {"id": 9, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}
ACUDIENTE = {"id": 3, "rol": "acudiente"}


@pytest.fixture(autouse=True)
def guardia_del_anio(monkeypatch):
    """Año lectivo, paso 3.7: al editar, la guardia de escritura mira el año de
    la anotacion antes de escribir. Se dobla aqui, asi que no suma en los
    conteos de este archivo (en produccion es una consulta mas; la cuenta
    `test_anio_lectivo_guardia_conteos.py`). Sus pruebas viven en
    `test_anio_lectivo_guardia.py`; aqui solo se anota a quien se le pidio.
    Crear no la lleva: la anotacion nueva nace siempre en el año activo."""
    llamadas = []
    monkeypatch.setattr(
        observador,
        "exigir_anotacion_editable",
        lambda _cursor, anotacion_id, usuario: llamadas.append((anotacion_id, usuario)),
    )
    return llamadas


@pytest.fixture(autouse=True)
def sin_firma_del_acudiente(monkeypatch):
    """Firma del acudiente (`docs/funcionalidades/FIRMA_OBSERVADOR.md`): al
    editar, se bloquea la anotacion y se mira si ya tiene firma, porque lo
    firmado no se edita. Se dobla aqui como la guardia del año: ninguna
    anotacion de este archivo esta firmada, y asi los `fetchone` de cada prueba
    siguen siendo los de siempre. Lo firmado y su 409 viven en
    `test_observador_firma.py`."""
    llamadas = []

    def no_esta_firmada(_cursor, anotacion_id):
        llamadas.append(anotacion_id)
        return False

    monkeypatch.setattr(
        observador.observador_repository,
        "bloquear_y_saber_si_esta_firmada",
        no_esta_firmada,
    )
    return llamadas


class CursorFalso:
    def __init__(self, respuestas=None):
        self.respuestas = list(respuestas or [])
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.respuestas.pop(0) if self.respuestas else None

    def fetchall(self):
        return []


class ConexionFalsa:
    def __init__(self):
        self.cursor_obj = CursorFalso([(1,)])

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def close(self):
        pass


class ContadorDeConexiones:
    def __init__(self):
        self.abiertas = 0

    def __call__(self):
        self.abiertas += 1
        return ConexionFalsa()


def cursor_de(monkeypatch, respuestas):
    """`respuestas` alimenta los `fetchone` en orden. El primero suele ser el
    del permiso, y el siguiente el de la escritura."""
    cursor = CursorFalso(respuestas)
    commits = []

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        commits.append(commit)
        yield cursor

    monkeypatch.setattr(observador, "get_cursor", fake_get_cursor)
    cursor.commits = commits
    return cursor


def anotacion_nueva(**cambios):
    datos = {
        "estudiante_id": 55,
        "periodo": 1,
        "conductual": "se para mucho.hace desorden",
    }
    datos.update(cambios)
    return AnotacionCreate(**datos)


def edicion(**cambios):
    datos = {"conductual": "ya mejoro"}
    datos.update(cambios)
    return AnotacionUpdate(**datos)


# ---------------------------------------------------------------------------
# Quien puede escribir
# ---------------------------------------------------------------------------


def test_un_profesor_del_alumno_crea_una_anotacion(monkeypatch):
    cursor = cursor_de(monkeypatch, [(1,), (99,)])

    resultado = observador.crear_anotacion(anotacion_nueva(), PROFESOR)

    assert resultado == {"id": 99}
    assert cursor.commits == [True], "una escritura tiene que confirmar"


def test_el_autor_sale_del_token_y_no_del_cuerpo(monkeypatch):
    """Invariante 4. Si `profesor_id` viajara en el cuerpo, un profesor podria
    firmar una anotacion con el nombre de otro."""
    cursor = cursor_de(monkeypatch, [(1,), (99,)])

    observador.crear_anotacion(anotacion_nueva(), PROFESOR)

    _consulta, parametros = cursor.calls[-1]
    assert parametros[1] == 7, "el profesor_id es el del token"


def test_mandar_profesor_id_en_el_cuerpo_no_hace_nada():
    """El esquema no lo declara, asi que Pydantic lo descarta en silencio. Se
    fija por prueba para que nadie lo anada 'por comodidad'."""
    datos = anotacion_nueva()

    assert not hasattr(datos, "profesor_id")
    assert "profesor_id" not in AnotacionCreate.model_fields


def test_un_profesor_que_no_comparte_curso_no_puede_escribir(monkeypatch):
    cursor_de(monkeypatch, [None])

    with pytest.raises(HTTPException) as exc:
        observador.crear_anotacion(anotacion_nueva(), PROFESOR)

    assert exc.value.status_code == 403


def test_el_admin_no_puede_crear_una_anotacion(monkeypatch):
    """No es un descuido, es la razon por la que existe `_profesor_que_escribe`.

    El `id` de un admin sale de `usuarios`, no de `profesor`. Usarlo como autor
    firmaria la anotacion con el profesor que tenga ese mismo numero. Al
    escribir esto, en `tenant_colegio_1` la administradora tiene `usuarios.id=1`
    y el profesor 1 es OTRA persona: la anotacion habria quedado a su nombre,
    sin error y sin aviso.
    """
    cursor = cursor_de(monkeypatch, [(1,), (99,)])

    with pytest.raises(HTTPException) as exc:
        observador.crear_anotacion(anotacion_nueva(), ADMIN)

    assert exc.value.status_code == 403
    assert cursor.calls == [], "ni siquiera debe abrir la escritura"


def test_un_rol_cualquiera_no_puede_escribir(monkeypatch):
    cursor_de(monkeypatch, [(1,), (99,)])

    with pytest.raises(HTTPException) as exc:
        observador.crear_anotacion(anotacion_nueva(), ACUDIENTE)

    assert exc.value.status_code == 403


def test_crear_pide_una_sola_conexion_al_pool(monkeypatch):
    """El guard corre sobre el cursor que ya abrio la ruta, igual que en la
    lectura."""
    cursor_de(monkeypatch, [(1,), (99,)])
    contador = ContadorDeConexiones()
    monkeypatch.setattr(permissions, "get_connection", contador)

    observador.crear_anotacion(anotacion_nueva(), PROFESOR)

    assert contador.abiertas == 0


# ---------------------------------------------------------------------------
# Que se guarda
# ---------------------------------------------------------------------------


def test_es_una_bitacora_y_nunca_pisa_lo_anterior(monkeypatch):
    """El defecto que esta funcionalidad vino a corregir. La tabla vieja usaba
    un UPSERT contra su UNIQUE y cada guardado borraba el anterior."""
    cursor = cursor_de(monkeypatch, [(1,), (99,)])

    observador.crear_anotacion(anotacion_nueva(), PROFESOR)

    consulta = cursor.calls[-1][0].upper()
    assert "INSERT INTO OBSERVADOR_ANOTACIONES" in consulta
    assert "ON CONFLICT" not in consulta
    assert "UPDATE" not in consulta


def test_el_texto_se_guarda_ya_corregido():
    """Decidido el 2026-09-08: lo que la profesora ve y aprueba es lo que queda
    escrito, y lo que se imprime."""
    datos = anotacion_nueva(conductual="se para mucho.hace desorden")

    assert datos.conductual == "Se para mucho. Hace desorden"


def test_una_anotacion_vacia_no_se_guarda():
    """Se conserva la validacion de la tabla vieja. Es un 422 y no un 500
    porque vive en el esquema: bajarla al repositorio la convertiria en error
    del servidor."""
    with pytest.raises(ValidationError):
        anotacion_nueva(conductual="", cognitivo="", lenguaje="")


def test_un_espacio_en_blanco_no_cuenta_como_contenido():
    with pytest.raises(ValidationError):
        anotacion_nueva(conductual="   ", cognitivo="", lenguaje="")


@pytest.mark.parametrize("periodo", [0, 5, 99, -1])
def test_un_periodo_imposible_se_rechaza_antes_de_llegar_a_la_base(periodo):
    """Mismo rango que el CHECK de la tabla. Sin esto reventaria en PostgreSQL
    y saldria como 500 en vez de como un aviso util."""
    with pytest.raises(ValidationError):
        anotacion_nueva(periodo=periodo)


def test_la_materia_no_se_escribe(monkeypatch):
    """Por ahora no se rellena: el servidor no puede deducirla y preguntarla es
    friccion. La columna existe y se queda en su valor por defecto."""
    cursor = cursor_de(monkeypatch, [(1,), (99,)])

    observador.crear_anotacion(anotacion_nueva(), PROFESOR)

    assert "materia" not in cursor.calls[-1][0]
    assert "materia" not in AnotacionCreate.model_fields


def test_la_marca_de_positiva_o_negativa_no_se_pide_ni_se_escribe(monkeypatch):
    """El usuario la quito el 2026-09-09. Antes era obligatoria.

    Como `materia`, la columna **no se borra** de la tabla: deja de pedirse y de
    rellenarse, y la fila nace con `NULL`. Si algun dia vuelve, no hace falta
    otra migracion.
    """
    cursor = cursor_de(monkeypatch, [(1,), (99,)])

    observador.crear_anotacion(anotacion_nueva(), PROFESOR)

    assert "positiva" not in cursor.calls[-1][0]
    assert "positiva" not in AnotacionCreate.model_fields
    assert "positiva" not in AnotacionUpdate.model_fields


def test_mandar_la_marca_en_el_cuerpo_no_hace_nada():
    """Un cliente sin actualizar puede seguir mandandola: Pydantic la descarta.

    Se fija por prueba porque es lo que permite publicar el backend antes que la
    pantalla, que es el orden obligatorio en este proyecto.
    """
    datos = anotacion_nueva(positiva=True)

    assert not hasattr(datos, "positiva")


def test_editar_no_toca_la_marca_que_ya_tuviera(monkeypatch):
    """Antes la sobrescribia en cada edicion.

    Eso obligaba a ponerle una marca a una anotacion heredada que no la tenia,
    solo por corregirle una tilde. Ahora la fila conserva la suya.
    """
    cursor = cursor_de(monkeypatch, [(12,)])

    observador.editar_anotacion(12, edicion(), PROFESOR)

    consulta = cursor.calls[-1][0]
    assert "positiva" not in consulta
    assert "editada_en" in consulta, "el rastro de la edicion si se sigue fijando"


# ---------------------------------------------------------------------------
# Editar: solo el autor, y siempre deja rastro
# ---------------------------------------------------------------------------


def test_el_autor_edita_su_propia_anotacion(monkeypatch):
    cursor = cursor_de(monkeypatch, [(12,)])

    resultado = observador.editar_anotacion(12, edicion(), PROFESOR)

    assert resultado == {"id": 12}
    assert cursor.commits == [True]


def test_editar_deja_siempre_rastro(monkeypatch):
    """Invariante 2. Va en la misma sentencia que la escritura para que no
    dependa de que alguien se acuerde de fijarlo."""
    cursor = cursor_de(monkeypatch, [(12,)])

    observador.editar_anotacion(12, edicion(), PROFESOR)

    consulta, parametros = cursor.calls[-1]
    assert "editada_en = now()" in consulta
    assert "editada_por = %s" in consulta
    assert 7 in parametros


def test_la_autoria_se_comprueba_en_la_misma_sentencia_que_escribe(monkeypatch):
    """Sin ventana entre comprobar y escribir, y sin una consulta de mas en el
    camino normal."""
    cursor = cursor_de(monkeypatch, [(12,)])

    observador.editar_anotacion(12, edicion(), PROFESOR)

    consulta, parametros = cursor.calls[-1]
    assert "WHERE id = %s AND profesor_id = %s" in consulta
    assert parametros[-2:] == (12, 7)
    assert len(cursor.calls) == 1, "el camino normal es una sola consulta"


def test_el_admin_no_puede_editar_la_anotacion_de_un_profesor(monkeypatch):
    """**Excepcion deliberada a la norma del proyecto.** Casi todos los guards
    empiezan con `if rol == "admin": return`. Aqui NO.

    Si el coordinador puede reescribir lo que anoto una profesora, la bitacora
    deja de servir como documento ante una reclamacion. Es el invariante 3, y
    el documento pide explicitamente una prueba que lo impida.
    """
    cursor = cursor_de(monkeypatch, [(12,)])

    with pytest.raises(HTTPException) as exc:
        observador.editar_anotacion(12, edicion(), ADMIN)

    assert exc.value.status_code == 403
    assert cursor.calls == [], "no debe llegar ni a intentar la escritura"


def test_un_profesor_no_puede_editar_la_de_otro(monkeypatch):
    """El `UPDATE` no toca ninguna fila porque el autor no coincide. Solo
    entonces se paga la segunda consulta, para saber si existe."""
    cursor = cursor_de(monkeypatch, [None, (7,)])

    with pytest.raises(HTTPException) as exc:
        observador.editar_anotacion(12, edicion(), OTRO_PROFESOR)

    assert exc.value.status_code == 403
    assert len(cursor.calls) == 2


def test_editar_una_anotacion_que_no_existe_da_404(monkeypatch):
    """Distinto de 403: «no existe» y «no es tuya» son cosas distintas, y
    decirlas al reves confunde a quien la escribio."""
    cursor = cursor_de(monkeypatch, [None, None])

    with pytest.raises(HTTPException) as exc:
        observador.editar_anotacion(12, edicion(), PROFESOR)

    assert exc.value.status_code == 404
    assert len(cursor.calls) == 2, "el UPDATE no toca nada, y luego se pregunta si existe"


def test_la_edicion_no_cambia_de_estudiante_ni_de_periodo():
    """Se corrige como se conto, no cuando paso."""
    assert "estudiante_id" not in AnotacionUpdate.model_fields
    assert "periodo" not in AnotacionUpdate.model_fields


def test_el_texto_editado_tambien_se_guarda_corregido():
    assert edicion(conductual="ya mejoro.mucho").conductual == "Ya mejoro. Mucho"


def test_una_edicion_no_puede_vaciar_la_anotacion():
    with pytest.raises(ValidationError):
        edicion(conductual="", cognitivo="", lenguaje="")


# ---------------------------------------------------------------------------
# Nadie borra
# ---------------------------------------------------------------------------


def test_no_existe_endpoint_de_borrado():
    """Invariante 1. No hay `DELETE` y no debe anadirse sin una orden explicita
    del usuario."""
    metodos = set()
    for ruta in observador.router.routes:
        metodos |= set(getattr(ruta, "methods", set()))

    assert "DELETE" not in metodos
    assert metodos <= {"GET", "POST", "PUT", "HEAD", "OPTIONS"}


def test_el_repositorio_no_sabe_borrar():
    """La otra mitad: aunque alguien anadiera la ruta, no hay nada que llamar."""
    fuente = (
        observador.observador_repository.__file__
    )
    with open(fuente, encoding="utf-8") as archivo:
        codigo = archivo.read().upper()

    assert "DELETE FROM" not in codigo


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "accion",
    [
        lambda: observador.crear_anotacion(anotacion_nueva(), PROFESOR),
        lambda: observador.editar_anotacion(12, edicion(), PROFESOR),
    ],
)
def test_un_fallo_de_base_no_filtra_el_mensaje_de_postgresql(monkeypatch, caplog, accion):
    secreto = "FATAL: password authentication failed for user admin"

    @contextmanager
    def revienta(commit=False, cursor_factory=None):
        raise RuntimeError(secreto)
        yield  # pragma: no cover

    monkeypatch.setattr(observador, "get_cursor", revienta)

    with caplog.at_level("ERROR"):
        with pytest.raises(HTTPException) as exc:
            accion()

    assert exc.value.status_code == 500
    assert secreto not in str(exc.value.detail)
    assert secreto in caplog.text
