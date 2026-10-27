"""Reglas puras de la firma del acudiente en el observador.

Ver `docs/funcionalidades/FIRMA_OBSERVADOR.md`. Sin HTTP ni base de datos: la
imagen, la version de lo que se muestra, la huella de lo que se firma, el
documento enmascarado y quien puede tomar una firma. Las usan la ruta, el
esquema y sus pruebas.
"""
import base64
import binascii
import hashlib
import json
from datetime import datetime, timezone

FIRMA_PNG = b"\x89PNG\r\n\x1a\n"
MAX_BYTES_IMAGEN = 100 * 1024
MAX_LADO_IMAGEN = 2000
PREFIJO_DATA_URL = "data:image/png;base64,"

MENSAJE_IMAGEN_INVALIDA = "La firma no es una imagen válida. Pide que firme de nuevo."
MENSAJE_IMAGEN_GRANDE = "La firma es demasiado grande. Pide que firme de nuevo."

# El orden no importa (el texto canonico ordena las claves), pero la lista si:
# quitar un campo de aqui dejaria cambiarlo sin que la huella lo note.
CAMPOS_DE_LA_ANOTACION = (
    "id",
    "estudiante_id",
    "profesor_id",
    "periodo",
    "conductual",
    "cognitivo",
    "lenguaje",
    "creada_en",
    "editada_en",
)
CAMPOS_DE_LA_FIRMA = (
    "firmante_nombre",
    "firmante_tipo_documento",
    "firmante_documento",
    "firmante_parentesco",
    "tomada_por_profesor_id",
    "tomada_por_usuario_id",
    "tomada_por_nombre",
    "firmada_en",
)


class ImagenFirmaInvalidaError(ValueError):
    """La imagen no es un PNG aceptable. Su mensaje se puede mostrar.

    Es un `ValueError` para que, lanzado desde el esquema, Pydantic lo
    convierta en un 422 con ese mensaje.
    """


def decodificar_imagen(texto):
    """Los bytes del PNG de la firma, o `ImagenFirmaInvalidaError`.

    Acepta el base64 con o sin el prefijo `data:image/png;base64,` que produce
    `canvas.toDataURL()`. Comprueba lo justo para no guardar cualquier cosa: que
    sea base64 de verdad, que empiece como un PNG, que no pase de 100 KB y que
    su ancho y alto sean razonables. No interpreta el resto del archivo.
    """
    if not isinstance(texto, str):
        raise ImagenFirmaInvalidaError(MENSAJE_IMAGEN_INVALIDA)
    if texto.startswith(PREFIJO_DATA_URL):
        texto = texto[len(PREFIJO_DATA_URL):]
    try:
        datos = base64.b64decode(texto, validate=True)
    except (binascii.Error, ValueError):
        raise ImagenFirmaInvalidaError(MENSAJE_IMAGEN_INVALIDA) from None

    if len(datos) > MAX_BYTES_IMAGEN:
        raise ImagenFirmaInvalidaError(MENSAJE_IMAGEN_GRANDE)
    # La firma PNG (8 bytes) y la cabecera IHDR: largo (4), tipo (4), ancho (4)
    # y alto (4). Un PNG siempre empieza asi.
    if len(datos) < 24 or not datos.startswith(FIRMA_PNG) or datos[12:16] != b"IHDR":
        raise ImagenFirmaInvalidaError(MENSAJE_IMAGEN_INVALIDA)
    ancho = int.from_bytes(datos[16:20], "big")
    alto = int.from_bytes(datos[20:24], "big")
    if not (0 < ancho <= MAX_LADO_IMAGEN and 0 < alto <= MAX_LADO_IMAGEN):
        raise ImagenFirmaInvalidaError(MENSAJE_IMAGEN_INVALIDA)
    return datos


def sha256_de_imagen(datos):
    """El SHA-256 de la imagen en hexadecimal, igual que
    `encode(sha256(imagen_png), 'hex')` en PostgreSQL."""
    return hashlib.sha256(bytes(datos)).hexdigest()


def _valor_canonico(valor):
    # Las fechas, siempre en UTC e ISO: una misma hora leida con otra zona
    # horaria no puede cambiar la huella.
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).isoformat()
    return valor


def _canonico(datos):
    """Un texto unico para los mismos datos: claves ordenadas, sin espacios."""
    return json.dumps(
        {clave: _valor_canonico(valor) for clave, valor in datos.items()},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _sha256(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def version_de_anotacion(anotacion):
    """Una huella corta del contenido de la anotacion, la que se muestra.

    La pantalla la recibe con la bitacora y la devuelve al firmar. Si la
    anotacion cambio entre medias, ya no coincide y la firma se rechaza con
    409: nadie firma un texto distinto del que leyo.
    """
    contenido = {campo: anotacion[campo] for campo in CAMPOS_DE_LA_ANOTACION}
    return _sha256(_canonico(contenido))[:16]


def calcular_huella(anotacion, firma, imagen_sha256):
    """El SHA-256 de todo lo firmado: la anotacion, la firma y su imagen.

    Se calcula al firmar y se guarda. En cada lectura se vuelve a calcular: si
    no coincide, algo cambio despues de firmar sin pasar por la API, y la
    firma sale con `integra: false`.
    """
    datos = {f"anotacion_{campo}": anotacion[campo] for campo in CAMPOS_DE_LA_ANOTACION}
    datos.update({campo: firma[campo] for campo in CAMPOS_DE_LA_FIRMA})
    datos["imagen_sha256"] = imagen_sha256
    return _sha256(_canonico(datos))


def huella_coincide(anotacion, firma, imagen_sha256, huella_guardada):
    """Si la huella guardada sigue cubriendo lo que hay hoy."""
    if not huella_guardada or not imagen_sha256:
        return False
    return calcular_huella(anotacion, firma, imagen_sha256) == huella_guardada.strip()


def enmascarar_documento(documento):
    """El documento con todo oculto menos los ultimos cuatro caracteres.

    Para la pantalla: la bitacora la ven todos los profesores del alumno, y no
    necesitan el documento completo del acudiente. El impreso si lo lleva.
    """
    texto = (documento or "").strip()
    visibles = texto[-4:] if len(texto) > 4 else ""
    return "*" * (len(texto) - len(visibles)) + visibles


def puede_tomar_firma(usuario, autor_id, director_grupo_id):
    """Decision 3: el admin, el autor de la anotacion o el director de grupo.

    Es una regla sobre **quien toma** la firma, no sobre quien escribe: el admin
    no escribe ni edita anotaciones, pero si puede dejar constancia de que el
    acudiente leyo una. Su `id` sale de `usuarios`, asi que nunca se compara
    con el autor ni con el director, que son ids de `profesor`.
    """
    rol = usuario.get("rol")
    if rol == "admin":
        return True
    if rol != "profesor":
        return False
    return usuario.get("id") in (autor_id, director_grupo_id)
