"""Reglas puras de las firmas guardadas para el boletin.

Ver `docs/funcionalidades/FIRMAS_BOLETIN.md`. Sin HTTP ni base de datos: que la
imagen sea un PNG aceptable y como sale hacia la pantalla.

La revision de la imagen es la misma de la firma del acudiente
(`app.core.firma_observador.decodificar_imagen`): PNG de verdad, hasta 100 KB y
lados razonables. Solo cambian los mensajes, porque aqui no hay un acudiente al
que pedirle que firme de nuevo: quien guarda es el admin o el propio profesor.
"""
import base64

from app.core.firma_observador import (
    MENSAJE_IMAGEN_GRANDE,
    PREFIJO_DATA_URL,
    ImagenFirmaInvalidaError,
    decodificar_imagen,
)

MENSAJE_FIRMA_INVALIDA = "La firma no es una imagen válida. Vuelve a firmar o sube otra foto."
MENSAJE_FIRMA_GRANDE = "La firma pesa demasiado. Vuelve a firmar o sube otra foto."


def decodificar_firma(texto):
    """Los bytes del PNG de la firma, o `ImagenFirmaInvalidaError` con un
    mensaje que se puede mostrar.

    Acepta el base64 con o sin el prefijo `data:image/png;base64,`.
    """
    try:
        return decodificar_imagen(texto)
    except ImagenFirmaInvalidaError as error:
        grande = str(error) == MENSAJE_IMAGEN_GRANDE
        raise ImagenFirmaInvalidaError(
            MENSAJE_FIRMA_GRANDE if grande else MENSAJE_FIRMA_INVALIDA
        ) from None


def a_data_url(imagen_png):
    """La imagen lista para un `<img src>`, o `None` si no hay firma.

    psycopg2 entrega `bytea` como `memoryview`; tambien acepta `bytes`.
    """
    if imagen_png is None:
        return None
    return PREFIJO_DATA_URL + base64.b64encode(bytes(imagen_png)).decode("ascii")


def firma_para_responder(imagen_png, actualizado_en):
    """Lo que devuelven las rutas de `/firmas`: la imagen y cuando se guardo.

    Sin firma, los dos van en `None`: la pantalla muestra "Sin firma
    guardada" sin tener que distinguir un 404.
    """
    if imagen_png is None:
        return {"imagen": None, "actualizado_en": None}
    return {
        "imagen": a_data_url(imagen_png),
        "actualizado_en": actualizado_en.isoformat() if actualizado_en else None,
    }
