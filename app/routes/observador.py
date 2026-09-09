"""Bitacora del observador del estudiante.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Fase 2: **solo lectura**.
Todavia no existen `POST` ni `PUT`, y `DELETE` no existira nunca: nadie borra
una anotacion, es el invariante 1 del documento.

Convive con `app/routes/observaciones.py`, que sirve la pantalla vieja. Esa
sigue funcionando y no se toca hasta que esta este verificada.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import require_estudiante_access
from app.database import get_cursor
from app.dependencies import get_current_user
from app.repositories import observador_repository

logger = logging.getLogger(__name__)

# ATENCION: el frontend muestra este texto tal cual en un aviso, igual que en
# `observaciones.py`. Es una constante y NUNCA `str(e)`: ahi saldria el mensaje
# de PostgreSQL, con nombres internos, en la pantalla de una profesora.
_ERROR_CONSULTAR = "No se pudo consultar el observador. Intenta de nuevo."
_ERROR_NO_EXISTE = "No encontramos a ese estudiante."

router = APIRouter(tags=["Observador"], dependencies=[Depends(get_current_user)])


def _anotacion(fila):
    """Una fila de la consulta, con la forma que consume el frontend.

    `profesor_id` viaja para que la pantalla decida si pinta el boton Editar.
    Es **comodidad visual**: la regla de verdad la impone el servidor, y el
    frontend no puede ser la unica defensa.
    """
    (
        _nivel,
        anotacion_id,
        profesor_id,
        nombre,
        apellido,
        materia,
        periodo,
        positiva,
        conductual,
        cognitivo,
        lenguaje,
        creada_en,
        editada_en,
        editada_por,
    ) = fila

    return {
        "id": anotacion_id,
        "profesor_id": profesor_id,
        # `nombre` y `apellido` son nulables en el esquema, asi que se descartan
        # los vacios en vez de imprimir "Ana None".
        "profesor": " ".join(parte for parte in (nombre, apellido) if parte),
        "materia": materia,
        "periodo": periodo,
        "positiva": positiva,
        "conductual": conductual,
        "cognitivo": cognitivo,
        "lenguaje": lenguaje,
        "creada_en": creada_en,
        "editada_en": editada_en,
        "editada_por": editada_por,
    }


@router.get("/observador/{estudiante_id}")
def obtener_observador(
    estudiante_id: int,
    periodo: int | None = Query(
        None,
        ge=1,
        le=4,
        description="Etiqueta opcional. Sin ella devuelve el ano entero.",
    ),
    current_user: dict = Depends(get_current_user),
):
    """La bitacora completa de un estudiante, la anotacion mas nueva primero.

    Devuelve el `nivel` del curso junto a las anotaciones, y no dentro de cada
    una: es del alumno, no de la anotacion. Va fuera **porque tiene que llegar
    aunque no haya ninguna anotacion**, que hoy es el caso de todos los alumnos.
    La pantalla lo necesita para decidir si muestra la materia: preescolar la
    omite y dice el nivel en el titulo, primaria la lleva en capsula, y un curso
    sin nivel se comporta como primaria.

    Sin `periodo` devuelve **todas**, que es el caso por defecto: cambiar de
    periodo en la pantalla no puede ocultar historial.

    Quien puede leerla: cualquier profesor que comparta curso con el alumno, y
    el admin siempre. Un profesor ve **todas** las anotaciones, tambien las de
    sus companeros: el observador es un documento del colegio sobre el nino, no
    el cuaderno privado de cada docente.
    """
    # El guard corre sobre el MISMO cursor que despues lee, igual que en la
    # lectura de `observaciones.py` desde el 2026-09-03: si abriera el suyo,
    # serian dos arranques de conexion y cada arranque cuesta dos consultas
    # extra antes de la util.
    #
    # Que este DENTRO del `try` no convierte su 403 en 500: el primer `except`
    # deja pasar toda HTTPException intacta y va antes que el generico. Hay
    # prueba que lo fija sobre una respuesta HTTP real.
    try:
        with get_cursor() as cursor:
            require_estudiante_access(estudiante_id, current_user, cursor=cursor)
            filas = observador_repository.leer_bitacora(cursor, estudiante_id, periodo)

            # Sin filas el estudiante no existe. Uno real sin anotaciones trae
            # una fila de relleno, con el nivel y el resto en NULL.
            if not filas:
                raise HTTPException(status_code=404, detail=_ERROR_NO_EXISTE)
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Fallo al consultar el observador del estudiante %s, periodo %s",
            estudiante_id,
            periodo,
        )
        raise HTTPException(status_code=500, detail=_ERROR_CONSULTAR)

    return {
        "nivel": filas[0][0],
        # La fila de relleno del alumno sin anotaciones se reconoce por el `id`
        # nulo, y se descarta aqui: hacia fuera son cero anotaciones.
        "anotaciones": [_anotacion(fila) for fila in filas if fila[1] is not None],
    }
