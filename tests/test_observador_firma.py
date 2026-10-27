"""Firma del acudiente en el observador.

Ver `docs/funcionalidades/FIRMA_OBSERVADOR.md`. Como las del observador, varias
de estas pruebas protegen invariantes que, si se rompen, **no fallan de forma
visible**: la firma se guarda igual, solo que a nombre de otro, con una hora que
eligio el navegador o sobre un texto que el acudiente no leyo. Una firma que no
se puede defender ante una reclamacion no sirve para lo que existe.
"""
import base64
import struct
import zlib
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from psycopg2.errors import UniqueViolation
from pydantic import ValidationError

from app.core import firma_observador as reglas
from app.repositories import observador_repository
from app.routes import observador
from app.schemas.observador import AnotacionUpdate, FirmaAnotacionCreate
from app.services.anio_lectivo import MENSAJE_ANIO_CERRADO, MENSAJE_SOLO_ANIO_ACTIVO


PROFESOR = {"id": 7, "rol": "profesor"}  # autor de la anotacion
DIRECTOR = {"id": 30, "rol": "profesor"}  # director de grupo del alumno
OTRO_PROFESOR = {"id": 9, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}
ACUDIENTE = {"id": 3, "rol": "acudiente"}

CREADA = datetime(2026, 10, 20, 14, 3, tzinfo=timezone.utc)
AHORA = datetime(2026, 10, 27, 15, 0, tzinfo=timezone.utc)


def png(ancho=40, alto=20):
    """Un PNG de verdad, pequeno y en escala de grises."""

    def bloque(tipo, datos):
        control = zlib.crc32(tipo + datos) & 0xFFFFFFFF
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", control)

    cabecera = struct.pack(">IIBBBBB", ancho, alto, 8, 0, 0, 0, 0)
    filas = b"".join(b"\x00" + b"\xff" * ancho for _ in range(alto))
    return (
        reglas.FIRMA_PNG
        + bloque(b"IHDR", cabecera)
        + bloque(b"IDAT", zlib.compress(filas))
        + bloque(b"IEND", b"")
    )


def data_url(datos=None):
    return reglas.PREFIJO_DATA_URL + base64.b64encode(datos or png()).decode("ascii")


IMAGEN = png()
IMAGEN_SHA256 = reglas.sha256_de_imagen(IMAGEN)

# La anotacion 12 de Pepito (55), escrita por la profesora 7.
CONTENIDO = {
    "id": 12,
    "estudiante_id": 55,
    "profesor_id": 7,
    "periodo": 1,
    "conductual": "Se para mucho.",
    "cognitivo": "",
    "lenguaje": "",
    "creada_en": CREADA,
    "editada_en": None,
}
VERSION = reglas.version_de_anotacion(CONTENIDO)

# Su firma: la madre, ante la profesora.
FIRMA = {
    "firmante_nombre": "Maria Lopez",
    "firmante_tipo_documento": "CC",
    "firmante_documento": "52123456",
    "firmante_parentesco": "Madre",
    "tomada_por_profesor_id": 7,
    "tomada_por_usuario_id": None,
    "tomada_por_nombre": "Ana Gomez",
    "firmada_en": AHORA,
}
HUELLA = reglas.calcular_huella(CONTENIDO, FIRMA, IMAGEN_SHA256)


class CursorFalso:
    def __init__(self, respuestas=(), filas=(), falla_en=None):
        self.respuestas = list(respuestas)
        self.filas = list(filas)
        self.falla_en = falla_en
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if self.falla_en and self.falla_en[0] in query:
            raise self.falla_en[1]

    def fetchone(self):
        return self.respuestas.pop(0) if self.respuestas else None

    def fetchall(self):
        return list(self.filas)


def cursor_de(monkeypatch, respuestas=(), filas=(), falla_en=None):
    """`respuestas` alimenta los `fetchone` en orden: al firmar, la anotacion,
    el permiso del profesor (el admin no lo consulta) y el `INSERT`."""
    cursor = CursorFalso(respuestas, filas, falla_en)
    commits = []

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        commits.append(commit)
        yield cursor

    monkeypatch.setattr(observador, "get_cursor", fake_get_cursor)
    cursor.commits = commits
    return cursor


def fila_para_firmar(**cambios):
    """La fila de `leer_anotacion_para_firmar`, en el orden de su consulta."""
    datos = {
        **CONTENIDO,
        "anio": 2026,
        "estado": "activo",
        "director_grupo_id": 30,
        "firmada": False,
        "nombre_profesor": "Ana Gomez",
        "nombre_usuario": None,
        "ahora": AHORA,
    }
    datos.update(cambios)
    return tuple(
        datos[campo]
        for campo in (
            "id", "estudiante_id", "profesor_id", "periodo", "conductual",
            "cognitivo", "lenguaje", "creada_en", "editada_en", "anio", "estado",
            "director_grupo_id", "firmada", "nombre_profesor", "nombre_usuario",
            "ahora",
        )
    )


def firma_nueva(**cambios):
    datos = {
        "firmante_nombre": "  Maria   Lopez ",
        "firmante_tipo_documento": "CC",
        "firmante_documento": "52123456",
        "firmante_parentesco": "Madre",
        "imagen": data_url(IMAGEN),
        "version": VERSION,
    }
    datos.update(cambios)
    return FirmaAnotacionCreate(**datos)


def _insert(cursor):
    return next(
        params for sql, params in cursor.calls if "INSERT INTO observador_firmas" in sql
    )


def _hubo_insert(cursor):
    return any("INSERT INTO observador_firmas" in sql for sql, _ in cursor.calls)


# ---------------------------------------------------------------------------
# La imagen
# ---------------------------------------------------------------------------


def test_un_png_valido_se_acepta_con_o_sin_el_prefijo_data():
    assert reglas.decodificar_imagen(data_url(IMAGEN)) == IMAGEN
    assert reglas.decodificar_imagen(base64.b64encode(IMAGEN).decode()) == IMAGEN


@pytest.mark.parametrize(
    "texto",
    [
        "esto no es base64 %%%",
        base64.b64encode(b"GIF89a una imagen de otro tipo...........").decode(),
        base64.b64encode(b"\x89PNG\r\n\x1a\n corto").decode(),
        "",
    ],
    ids=["no-es-base64", "no-es-png", "png-cortado", "vacio"],
)
def test_lo_que_no_es_un_png_se_rechaza(texto):
    with pytest.raises(reglas.ImagenFirmaInvalidaError) as exc:
        reglas.decodificar_imagen(texto)
    assert str(exc.value) == reglas.MENSAJE_IMAGEN_INVALIDA


def test_una_imagen_de_mas_de_100_kb_se_rechaza():
    enorme = IMAGEN + b"\x00" * (reglas.MAX_BYTES_IMAGEN + 1 - len(IMAGEN))
    with pytest.raises(reglas.ImagenFirmaInvalidaError) as exc:
        reglas.decodificar_imagen(data_url(enorme))
    assert str(exc.value) == reglas.MENSAJE_IMAGEN_GRANDE


@pytest.mark.parametrize("ancho,alto", [(0, 20), (40, 0), (reglas.MAX_LADO_IMAGEN + 1, 20)])
def test_un_png_sin_tamano_o_desmedido_se_rechaza(ancho, alto):
    with pytest.raises(reglas.ImagenFirmaInvalidaError):
        reglas.decodificar_imagen(data_url(png(ancho, alto)))


# ---------------------------------------------------------------------------
# Version y huella
# ---------------------------------------------------------------------------


def test_la_version_es_estable_y_cambia_si_cambia_el_texto():
    assert reglas.version_de_anotacion(dict(CONTENIDO)) == VERSION
    editada = {**CONTENIDO, "conductual": "Ya mejoro.", "editada_en": AHORA}
    assert reglas.version_de_anotacion(editada) != VERSION


def test_la_misma_hora_en_otra_zona_horaria_no_cambia_nada():
    """La hora llega de PostgreSQL con la zona de la sesion. Leida en Bogota o
    en UTC es el mismo instante, y ni la version ni la huella pueden cambiar."""
    bogota = timezone(timedelta(hours=-5))
    en_bogota = {**CONTENIDO, "creada_en": CREADA.astimezone(bogota)}
    firma_en_bogota = {**FIRMA, "firmada_en": AHORA.astimezone(bogota)}

    assert reglas.version_de_anotacion(en_bogota) == VERSION
    assert reglas.calcular_huella(en_bogota, firma_en_bogota, IMAGEN_SHA256) == HUELLA


@pytest.mark.parametrize("campo", reglas.CAMPOS_DE_LA_ANOTACION)
def test_la_huella_cubre_cada_dato_de_la_anotacion(campo):
    cambiada = {**CONTENIDO, campo: "otro valor"}
    assert reglas.calcular_huella(cambiada, FIRMA, IMAGEN_SHA256) != HUELLA


@pytest.mark.parametrize("campo", reglas.CAMPOS_DE_LA_FIRMA)
def test_la_huella_cubre_cada_dato_de_la_firma(campo):
    cambiada = {**FIRMA, campo: "otro valor"}
    assert reglas.calcular_huella(CONTENIDO, cambiada, IMAGEN_SHA256) != HUELLA


def test_la_huella_cubre_la_imagen():
    otra = reglas.sha256_de_imagen(png(41, 20))
    assert reglas.calcular_huella(CONTENIDO, FIRMA, otra) != HUELLA


def test_la_huella_guardada_se_comprueba_contra_lo_que_hay_hoy():
    assert reglas.huella_coincide(CONTENIDO, FIRMA, IMAGEN_SHA256, HUELLA)
    tocada = {**CONTENIDO, "conductual": "Texto cambiado en la base."}
    assert not reglas.huella_coincide(tocada, FIRMA, IMAGEN_SHA256, HUELLA)
    assert not reglas.huella_coincide(CONTENIDO, FIRMA, None, HUELLA)


# ---------------------------------------------------------------------------
# Documento enmascarado y quien puede tomar la firma
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "documento,esperado",
    [("52123456", "****3456"), (" 52123456 ", "****3456"), ("1234", "****"), ("", ""), (None, "")],
)
def test_el_documento_se_enmascara_menos_los_ultimos_cuatro(documento, esperado):
    assert reglas.enmascarar_documento(documento) == esperado


@pytest.mark.parametrize(
    "usuario,puede",
    [
        (PROFESOR, True),  # el autor
        (DIRECTOR, True),  # el director de grupo
        (OTRO_PROFESOR, False),
        (ADMIN, True),
        (ACUDIENTE, False),
    ],
    ids=["autor", "director", "otro-profesor", "admin", "otro-rol"],
)
def test_toman_la_firma_el_autor_el_director_y_el_admin(usuario, puede):
    """Decision 3 del documento."""
    assert reglas.puede_tomar_firma(usuario, 7, 30) is puede


def test_un_curso_sin_director_no_le_da_permiso_a_nadie_mas():
    assert reglas.puede_tomar_firma(OTRO_PROFESOR, 7, None) is False


# ---------------------------------------------------------------------------
# El esquema
# ---------------------------------------------------------------------------


def test_el_esquema_quita_los_espacios_sobrantes():
    assert firma_nueva().firmante_nombre == "Maria Lopez"


@pytest.mark.parametrize(
    "campo", ["firmante_nombre", "firmante_tipo_documento", "firmante_documento", "firmante_parentesco"]
)
def test_un_dato_del_firmante_de_solo_espacios_se_rechaza(campo):
    with pytest.raises(ValidationError):
        firma_nueva(**{campo: "    "})


def test_una_imagen_que_no_sirve_es_un_422_con_su_mensaje():
    with pytest.raises(ValidationError) as exc:
        firma_nueva(imagen="no es una imagen")
    assert reglas.MENSAJE_IMAGEN_INVALIDA in str(exc.value)


def test_quien_toma_la_firma_y_la_hora_no_se_aceptan_del_cuerpo():
    """Invariante 4. Pydantic ignora lo que no declara."""
    firma = firma_nueva(
        tomada_por_profesor_id=99,
        tomada_por_nombre="Otra persona",
        firmada_en="2020-01-01T00:00:00Z",
    )
    datos = firma.model_dump()
    assert "tomada_por_profesor_id" not in datos
    assert "tomada_por_nombre" not in datos
    assert "firmada_en" not in datos


# ---------------------------------------------------------------------------
# Tomar la firma
# ---------------------------------------------------------------------------


def test_el_autor_toma_la_firma(monkeypatch):
    cursor = cursor_de(monkeypatch, [fila_para_firmar(), (1,), (99,)])

    respuesta = observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    assert respuesta["id"] == 99
    assert respuesta["anotacion_id"] == 12
    assert respuesta["firmante_nombre"] == "Maria Lopez"
    assert respuesta["firmante_documento_enmascarado"] == "****3456"
    assert "firmante_documento" not in respuesta
    assert respuesta["tomada_por_nombre"] == "Ana Gomez"
    assert respuesta["integra"] is True
    assert cursor.commits == [True]


def test_la_firma_guarda_lo_que_cubre_su_huella(monkeypatch):
    """La hora es la de la transaccion y el testigo, el del token: los dos los
    pone el servidor (invariante 4), y la huella guardada los cubre."""
    cursor = cursor_de(monkeypatch, [fila_para_firmar(), (1,), (99,)])

    observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    (
        anotacion_id,
        nombre,
        tipo_documento,
        documento,
        parentesco,
        imagen,
        tomada_por_profesor_id,
        tomada_por_usuario_id,
        tomada_por_nombre,
        firmada_en,
        huella,
    ) = _insert(cursor)
    assert anotacion_id == 12
    assert (nombre, tipo_documento, documento, parentesco) == (
        "Maria Lopez", "CC", "52123456", "Madre",
    )
    assert imagen == IMAGEN
    assert (tomada_por_profesor_id, tomada_por_usuario_id) == (7, None)
    assert tomada_por_nombre == "Ana Gomez"
    assert firmada_en == AHORA
    assert huella == HUELLA


def test_el_director_de_grupo_toma_la_firma_de_la_anotacion_de_otro(monkeypatch):
    cursor = cursor_de(
        monkeypatch, [fila_para_firmar(nombre_profesor="Luis Director"), (1,), (99,)]
    )

    observador.firmar_anotacion(12, firma_nueva(), DIRECTOR)

    assert _insert(cursor)[6:9] == (30, None, "Luis Director")


def test_el_admin_toma_la_firma_con_su_id_de_usuarios(monkeypatch):
    """El admin no comparte tabla con los profesores: su id va a
    `tomada_por_usuario_id`, nunca a la columna de `profesor`."""
    cursor = cursor_de(
        monkeypatch,
        [fila_para_firmar(nombre_profesor=None, nombre_usuario="Rectora"), (99,)],
    )

    observador.firmar_anotacion(12, firma_nueva(), ADMIN)

    assert _insert(cursor)[6:9] == (None, 1, "Rectora")
    sql, params = cursor.calls[0]
    assert params == (None, 1, 12)


def test_otro_profesor_no_puede_tomar_la_firma(monkeypatch):
    cursor = cursor_de(monkeypatch, [fila_para_firmar(), (1,)])

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), OTRO_PROFESOR)

    assert exc.value.status_code == 403
    assert not _hubo_insert(cursor)


def test_un_profesor_que_no_comparte_curso_no_puede_tomarla(monkeypatch):
    cursor = cursor_de(monkeypatch, [fila_para_firmar(), None])

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    assert exc.value.status_code == 403
    assert not _hubo_insert(cursor)


def test_un_rol_cualquiera_no_toca_la_base(monkeypatch):
    cursor = cursor_de(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), ACUDIENTE)

    assert exc.value.status_code == 403
    assert cursor.calls == []


def test_firmar_una_anotacion_que_no_existe_da_404(monkeypatch):
    cursor_de(monkeypatch, [None])

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(404, firma_nueva(), PROFESOR)

    assert exc.value.status_code == 404


def test_una_anotacion_ya_firmada_no_se_firma_otra_vez(monkeypatch):
    """Invariante 1: como maximo una firma por anotacion."""
    cursor = cursor_de(monkeypatch, [fila_para_firmar(firmada=True), (1,)])

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    assert exc.value.status_code == 409
    assert exc.value.detail == observador._ERROR_YA_FIRMADA
    assert not _hubo_insert(cursor)


def test_no_se_firma_un_texto_distinto_del_que_se_mostro(monkeypatch):
    """La autora corrigio la anotacion despues de que la pantalla la mostro: la
    version ya no coincide y la firma se rechaza."""
    editada = fila_para_firmar(conductual="Ya mejoro.", editada_en=AHORA)
    cursor = cursor_de(monkeypatch, [editada, (1,)])

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    assert exc.value.status_code == 409
    assert exc.value.detail == observador._ERROR_CAMBIO_AL_FIRMAR
    assert not _hubo_insert(cursor)


def test_si_dos_firman_a_la_vez_la_segunda_da_409(monkeypatch):
    """Las dos leyeron la anotacion sin firma; el UNIQUE para a la segunda."""
    cursor_de(
        monkeypatch,
        [fila_para_firmar(), (1,)],
        falla_en=("INSERT INTO observador_firmas", UniqueViolation()),
    )

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    assert exc.value.status_code == 409
    assert exc.value.detail == observador._ERROR_YA_FIRMADA


@pytest.mark.parametrize("usuario", [PROFESOR, ADMIN], ids=["profesor", "admin"])
def test_en_un_anio_cerrado_no_firma_nadie(monkeypatch, usuario):
    cursor = cursor_de(monkeypatch, [fila_para_firmar(estado="cerrado"), (1,)])

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), usuario)

    assert exc.value.status_code == 409
    assert exc.value.detail == MENSAJE_ANIO_CERRADO.format(anio=2026)
    assert not _hubo_insert(cursor)


def test_un_profesor_solo_firma_en_el_anio_activo(monkeypatch):
    """La misma regla de año que editar: en un año reabierto, solo el admin."""
    cursor_de(monkeypatch, [fila_para_firmar(estado="reabierto"), (1,)])
    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), PROFESOR)
    assert exc.value.status_code == 403
    assert exc.value.detail == MENSAJE_SOLO_ANIO_ACTIVO

    cursor_de(monkeypatch, [fila_para_firmar(estado="reabierto"), (99,)])
    assert observador.firmar_anotacion(12, firma_nueva(), ADMIN)["id"] == 99


def test_la_anotacion_se_bloquea_al_leerla_para_firmar(monkeypatch):
    cursor = cursor_de(monkeypatch, [fila_para_firmar(), (1,), (99,)])

    observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    sql, params = cursor.calls[0]
    assert "FOR UPDATE OF a" in sql
    assert params == (7, None, 12)


def test_un_fallo_de_base_no_deja_el_documento_ni_la_imagen_en_el_log(monkeypatch, caplog):
    """Invariante 6. El mensaje de PostgreSQL puede traer la fila entera."""
    mensaje_de_postgres = (
        'new row violates check constraint. DETAIL: Failing row contains '
        '(1, 12, Maria Lopez, CC, 52123456, Madre, \\x89504e47...)'
    )
    cursor_de(
        monkeypatch,
        [fila_para_firmar(), (1,)],
        falla_en=("INSERT INTO observador_firmas", RuntimeError(mensaje_de_postgres)),
    )

    with pytest.raises(HTTPException) as exc:
        observador.firmar_anotacion(12, firma_nueva(), PROFESOR)

    assert exc.value.status_code == 500
    assert exc.value.detail == observador._ERROR_FIRMAR
    assert "52123456" not in caplog.text
    assert "Failing row" not in caplog.text
    assert "RuntimeError" in caplog.text


# ---------------------------------------------------------------------------
# Lo firmado no se edita
# ---------------------------------------------------------------------------


def test_una_anotacion_firmada_no_se_edita(monkeypatch):
    """Invariante 2: ni su autora. Se corrige con una anotacion nueva."""
    escritas = []
    monkeypatch.setattr(observador, "exigir_anotacion_editable", lambda *_: None)
    monkeypatch.setattr(
        observador.observador_repository, "bloquear_y_saber_si_esta_firmada", lambda *_: True
    )
    monkeypatch.setattr(
        observador.observador_repository,
        "actualizar_anotacion_del_autor",
        lambda *args: escritas.append(args) or True,
    )
    cursor_de(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        observador.editar_anotacion(12, AnotacionUpdate(conductual="Otro texto"), PROFESOR)

    assert exc.value.status_code == 409
    assert exc.value.detail == observador._ERROR_FIRMADA_NO_SE_EDITA
    assert escritas == []


def test_editar_bloquea_la_anotacion_antes_de_mirar_la_firma():
    """Dos sentencias en un solo `execute`: primero el bloqueo, despues la
    firma. Asi una firma recien guardada se ve aunque se haya tenido que
    esperar (el motivo esta en el repositorio)."""
    cursor = CursorFalso([(True,)])

    assert observador_repository.bloquear_y_saber_si_esta_firmada(cursor, 12) is True

    [(sql, params)] = cursor.calls
    bloqueo, _, mirada = sql.partition(";")
    assert "FOR UPDATE" in bloqueo and "observador_firmas" not in bloqueo
    assert "observador_firmas" in mirada
    assert params == (12, 12)


def test_sin_firma_la_edicion_sigue_su_camino():
    cursor = CursorFalso([(False,)])
    assert observador_repository.bloquear_y_saber_si_esta_firmada(cursor, 12) is False


# ---------------------------------------------------------------------------
# La bitacora
# ---------------------------------------------------------------------------


def fila_bitacora(firma=None, **cambios):
    """Una fila de `leer_bitacora`, en el orden de su consulta."""
    datos = {
        "nivel": "primaria",
        "nombre": "Ana",
        "apellido": "Gomez",
        "materia": "",
        "positiva": None,
        "editada_por": None,
        "director_grupo_id": 30,
        "anio": 2026,
        "estado": "activo",
        **CONTENIDO,
    }
    datos.update(cambios)
    fila = tuple(
        datos[campo]
        for campo in (
            "nivel", "id", "profesor_id", "nombre", "apellido", "materia",
            "periodo", "positiva", "conductual", "cognitivo", "lenguaje",
            "creada_en", "editada_en", "editada_por", "director_grupo_id",
            "anio", "estado",
        )
    )
    if firma is None:
        return fila + (None,) * 10
    return fila + tuple(firma[campo] for campo in reglas.CAMPOS_DE_LA_FIRMA) + (
        firma.get("huella", HUELLA),
        firma.get("imagen_sha256", IMAGEN_SHA256),
    )


def _bitacora(monkeypatch, usuario, fila):
    cursor = cursor_de(monkeypatch, [(1,)], filas=[fila])
    return observador.obtener_observador(55, None, usuario)["anotaciones"][0], cursor


def test_la_bitacora_trae_la_firma_sin_imagen_y_con_el_documento_enmascarado(monkeypatch):
    anotacion, _ = _bitacora(monkeypatch, PROFESOR, fila_bitacora(firma=FIRMA))

    assert anotacion["firma"] == {
        "firmante_nombre": "Maria Lopez",
        "firmante_tipo_documento": "CC",
        "firmante_documento_enmascarado": "****3456",
        "firmante_parentesco": "Madre",
        "firmada_en": AHORA,
        "tomada_por_nombre": "Ana Gomez",
        "integra": True,
    }
    assert anotacion["puede_firmar"] is False


def test_una_firma_tocada_en_la_base_sale_como_no_integra(monkeypatch):
    """Alguien cambio el texto directamente en la base, saltandose la API: la
    huella guardada ya no lo cubre."""
    tocada = fila_bitacora(firma=FIRMA, conductual="Texto cambiado a mano.")

    anotacion, _ = _bitacora(monkeypatch, ADMIN, tocada)

    assert anotacion["firma"]["integra"] is False


def test_la_version_de_la_bitacora_es_la_que_acepta_la_firma(monkeypatch):
    anotacion, _ = _bitacora(monkeypatch, PROFESOR, fila_bitacora())

    assert anotacion["version"] == VERSION
    assert anotacion["firma"] is None


@pytest.mark.parametrize(
    "usuario,estado,puede",
    [
        (PROFESOR, "activo", True),
        (DIRECTOR, "activo", True),
        (OTRO_PROFESOR, "activo", False),
        (ADMIN, "activo", True),
        (ADMIN, "reabierto", True),
        (PROFESOR, "reabierto", False),
        (ADMIN, "cerrado", False),
        (PROFESOR, "cerrado", False),
    ],
)
def test_puede_firmar_dice_lo_mismo_que_dira_la_firma(monkeypatch, usuario, estado, puede):
    anotacion, _ = _bitacora(monkeypatch, usuario, fila_bitacora(estado=estado))

    assert anotacion["puede_firmar"] is puede


def test_la_firma_no_le_cuesta_otra_consulta_a_la_bitacora(monkeypatch):
    """La bitacora sigue siendo una consulta (mas la del permiso del
    profesor), y la imagen no viaja: solo su SHA-256 (invariante 7)."""
    _, cursor = _bitacora(monkeypatch, PROFESOR, fila_bitacora())

    assert len(cursor.calls) == 2
    sql = cursor.calls[-1][0]
    assert "LEFT JOIN observador_firmas f ON f.anotacion_id = a.id" in sql
    assert "encode(sha256(f.imagen_png), 'hex')" in sql
    assert sql.count("f.imagen_png") == 1


# ---------------------------------------------------------------------------
# Imprimir
# ---------------------------------------------------------------------------


def fila_para_imprimir(**cambios):
    datos = {**CONTENIDO, **FIRMA, "huella": HUELLA, "imagen": memoryview(IMAGEN)}
    datos.update(cambios)
    return tuple(datos[campo] for campo in reglas.CAMPOS_DE_LA_ANOTACION) + tuple(
        datos[campo] for campo in reglas.CAMPOS_DE_LA_FIRMA
    ) + (datos["huella"], datos["imagen"])


def test_imprimir_trae_la_imagen_y_el_documento_completo(monkeypatch):
    cursor_de(monkeypatch, [(1,)], filas=[fila_para_imprimir()])

    [firma] = observador.obtener_firmas_para_imprimir(55, None, PROFESOR)

    assert firma["anotacion_id"] == 12
    assert firma["firmante_documento"] == "52123456"
    assert firma["imagen"] == data_url(IMAGEN)
    assert firma["integra"] is True


def test_imprimir_avisa_si_la_imagen_cambio(monkeypatch):
    cursor_de(monkeypatch, [(1,)], filas=[fila_para_imprimir(imagen=memoryview(png(41, 20)))])

    [firma] = observador.obtener_firmas_para_imprimir(55, None, PROFESOR)

    assert firma["integra"] is False


def test_imprimir_tiene_la_misma_puerta_que_la_bitacora(monkeypatch):
    cursor_de(monkeypatch, [None])

    with pytest.raises(HTTPException) as exc:
        observador.obtener_firmas_para_imprimir(55, None, OTRO_PROFESOR)

    assert exc.value.status_code == 403


def test_imprimir_filtra_como_la_bitacora(monkeypatch):
    """Se imprime lo que se ve: el mismo periodo y el mismo año."""
    cursor = cursor_de(monkeypatch, [(1,)])

    observador.obtener_firmas_para_imprimir(55, 2, PROFESOR)

    sql, params = cursor.calls[-1]
    assert "a.anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')" in sql
    assert "a.periodo = %s" in sql
    assert params == (55, 2)


# ---------------------------------------------------------------------------
# Firmantes sugeridos
# ---------------------------------------------------------------------------

PADRES = ("Jose Lopez", "CC", "79111222", "Maria Lopez", "CC", "52123456")


def test_el_admin_ve_al_padre_y_a_la_madre(monkeypatch):
    cursor_de(monkeypatch, [PADRES + (False,)])

    assert observador.obtener_firmantes_sugeridos(55, ADMIN) == [
        {"parentesco": "Padre", "nombre": "Jose Lopez", "tipo_documento": "CC", "documento": "79111222"},
        {"parentesco": "Madre", "nombre": "Maria Lopez", "tipo_documento": "CC", "documento": "52123456"},
    ]


def test_solo_salen_los_padres_con_nombre(monkeypatch):
    cursor_de(monkeypatch, [("Jose Lopez", None, None, "   ", "CC", "52123456", False)])

    [padre] = observador.obtener_firmantes_sugeridos(55, ADMIN)

    assert padre == {"parentesco": "Padre", "nombre": "Jose Lopez", "tipo_documento": "", "documento": ""}


def test_quien_va_a_tomar_una_firma_ve_los_documentos(monkeypatch):
    """El director de grupo, o un profesor que le escribio una anotacion este
    año: la consulta lo resuelve y la ruta solo mira la ultima columna."""
    cursor = cursor_de(monkeypatch, [(1,), PADRES + (True,)])

    assert len(observador.obtener_firmantes_sugeridos(55, DIRECTOR)) == 2
    assert cursor.calls[-1][1] == (30, 30, 55)


def test_un_profesor_que_solo_comparte_curso_no_ve_los_documentos(monkeypatch):
    cursor_de(monkeypatch, [(1,), PADRES + (False,)])

    with pytest.raises(HTTPException) as exc:
        observador.obtener_firmantes_sugeridos(55, OTRO_PROFESOR)

    assert exc.value.status_code == 403


def test_los_firmantes_de_un_estudiante_que_no_existe_dan_404(monkeypatch):
    cursor_de(monkeypatch, [None])

    with pytest.raises(HTTPException) as exc:
        observador.obtener_firmantes_sugeridos(404, ADMIN)

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------


def test_una_firma_no_se_edita_ni_se_borra():
    """Invariante 3: no existe ninguna ruta que lo permita."""
    for ruta in observador.router.routes:
        if "firma" in getattr(ruta, "path", ""):
            assert ruta.methods <= {"GET", "POST"}, ruta.path
