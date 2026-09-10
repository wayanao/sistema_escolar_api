"""Bitacora del observador del estudiante.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Leer, crear y editar.
**`DELETE` no existe y no debe anadirse**: nadie borra una anotacion, es el
invariante 1 del documento. Hay prueba que lo impide.

Convive con `app/routes/observaciones.py`, que sirve la pantalla vieja. Esa
sigue funcionando y no se toca hasta que esta este verificada.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import require_estudiante_access
from app.database import get_cursor
from app.dependencies import get_current_user
from app.repositories import observador_repository
from app.schemas.observador import AnotacionCreate, AnotacionUpdate

logger = logging.getLogger(__name__)

# ATENCION: el frontend muestra este texto tal cual en un aviso, igual que en
# `observaciones.py`. Es una constante y NUNCA `str(e)`: ahi saldria el mensaje
# de PostgreSQL, con nombres internos, en la pantalla de una profesora.
_ERROR_CONSULTAR = "No se pudo consultar el observador. Intenta de nuevo."
_ERROR_NO_EXISTE = "No encontramos a ese estudiante."
_ERROR_GUARDAR = "No se pudo guardar la anotacion. Intenta de nuevo."
_ERROR_ANOTACION_NO_EXISTE = "Esa anotacion ya no existe."
_ERROR_SOLO_EL_AUTOR = "Solo quien escribio una anotacion puede editarla."
_ERROR_SOLO_PROFESORES = "Solo un profesor del estudiante puede escribir en el observador."
_ERROR_CONSULTAR_LISTA = "No se pudo consultar tu lista de estudiantes. Intenta de nuevo."
_ERROR_SOLO_PROFESORES_LISTA = "Solo un profesor tiene lista de estudiantes."

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


def _profesor_de_la_sesion(current_user):
    """El `profesor_id` de quien pide, o un 403 si no es profesor.

    **El admin tampoco tiene lista, y no es un descuido.** Su `id` sale de la
    tabla `usuarios`, no de `profesor`: usarlo aqui devolveria los alumnos del
    profesor que por casualidad tenga ese mismo numero. Es la misma trampa que
    documenta `_profesor_que_escribe`, y en `tenant_colegio_1` es real -la
    administradora tiene `usuarios.id = 1` y el profesor 1 es otra persona-.
    Ahi no saldria un error: saldria una lista de ninos ajenos con toda
    naturalidad.

    El admin entra al observador por la ficha del alumno, no por esta lista.
    """
    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=403, detail=_ERROR_SOLO_PROFESORES_LISTA)
    return current_user["id"]


# ATENCION: esta ruta va ANTES de `/observador/{estudiante_id}`, y el orden es
# obligatorio. Starlette prueba las rutas en el orden en que se declaran: si la
# parametrizada fuera primero, `/observador/mis-estudiantes` encajaria en ella,
# FastAPI intentaria convertir "mis-estudiantes" en `int` y devolveria un 422
# que no habria forma de entender. Hay prueba que fija el orden y otra que pide
# la ruta de verdad por HTTP.
@router.get("/observador/mis-estudiantes")
def listar_mis_estudiantes(current_user: dict = Depends(get_current_user)):
    """Los alumnos del profesor, de todos los cursos donde tiene clase.

    Existe para que la pantalla del observador **no dependa de una asignacion
    elegida**. El observador es del nino y no de la materia; la clase solo
    servia para saber a quien listar, y eso ataba la pantalla a una unica
    puerta de entrada.

    Devuelve el curso de cada alumno para poder agruparlos: un profesor puede
    tener 81 -medido-, y una lista plana de 81 nombres no se lee.

    **Una sola consulta**, con la misma regla que decide quien puede abrir cada
    bitacora. Ver `observador_repository.leer_estudiantes_del_profesor`.
    """
    profesor_id = _profesor_de_la_sesion(current_user)

    try:
        with get_cursor() as cursor:
            filas = observador_repository.leer_estudiantes_del_profesor(
                cursor, profesor_id
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Fallo al listar los estudiantes del profesor %s", profesor_id
        )
        raise HTTPException(status_code=500, detail=_ERROR_CONSULTAR_LISTA)

    # `estudiante_id` y no `id`: es el nombre que ya usa
    # `GET /planilla/{asignacion_id}`, la lista que esta reemplazando, asi que
    # la pantalla no tiene que traducir nada.
    return [
        {
            "estudiante_id": fila[0],
            "nombre": fila[1],
            "apellido": fila[2],
            "curso_id": fila[3],
            "curso": fila[4],
        }
        for fila in filas
    ]


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


def _profesor_que_escribe(current_user):
    """El `profesor_id` del autor, o un 403 si quien pide no es profesor.

    **El admin no escribe ni edita, y esto no es un descuido.** Su `id` sale de
    la tabla `usuarios`, no de `profesor`, asi que usarlo como autor firmaria la
    anotacion con el profesor que por casualidad tenga ese mismo numero. No es
    teorico: al escribir esto, en `tenant_colegio_1` la administradora tiene
    `usuarios.id = 1` y el profesor 1 es otra persona. Una bitacora que atribuye
    a alguien lo que no escribio no sirve ante una reclamacion.

    Se suma al invariante 3, que ya prohibia al admin editar lo de un profesor.
    """
    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=403, detail=_ERROR_SOLO_PROFESORES)
    return current_user["id"]


@router.post("/observador", status_code=201)
def crear_anotacion(data: AnotacionCreate, current_user: dict = Depends(get_current_user)):
    """Anade una anotacion a la bitacora de un estudiante.

    Nunca actualiza una existente: es una bitacora, y **todas quedan**. Un
    profesor puede anotar cuantas veces quiera en el mismo periodo, que es
    justo lo que el `UNIQUE` de la tabla vieja impedia.
    """
    profesor_id = _profesor_que_escribe(current_user)

    try:
        with get_cursor(commit=True) as cursor:
            require_estudiante_access(data.estudiante_id, current_user, cursor=cursor)

            anotacion_id = observador_repository.crear_anotacion(
                cursor,
                data.estudiante_id,
                profesor_id,
                data.periodo,
                data.positiva,
                data.conductual,
                data.cognitivo,
                data.lenguaje,
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Fallo al crear la anotacion del estudiante %s por el profesor %s",
            data.estudiante_id,
            profesor_id,
        )
        raise HTTPException(status_code=500, detail=_ERROR_GUARDAR)

    return {"id": anotacion_id}


@router.put("/observador/{anotacion_id}")
def editar_anotacion(
    anotacion_id: int,
    data: AnotacionUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Corrige una anotacion **propia**. Deja rastro de que se edito.

    No cambia de estudiante ni de periodo: se corrige como se conto, no cuando
    paso.
    """
    profesor_id = _profesor_que_escribe(current_user)

    try:
        with get_cursor(commit=True) as cursor:
            actualizada = observador_repository.actualizar_anotacion_del_autor(
                cursor,
                anotacion_id,
                profesor_id,
                data.positiva,
                data.conductual,
                data.cognitivo,
                data.lenguaje,
            )

            if not actualizada:
                # Solo aqui, en el camino de error, se paga una segunda
                # consulta: sirve para no decir «no es tuya» de algo que no
                # existe, ni «no existe» de algo que si.
                autor = observador_repository.leer_autor(cursor, anotacion_id)
                if autor is None:
                    raise HTTPException(
                        status_code=404, detail=_ERROR_ANOTACION_NO_EXISTE
                    )
                raise HTTPException(status_code=403, detail=_ERROR_SOLO_EL_AUTOR)
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Fallo al editar la anotacion %s por el profesor %s",
            anotacion_id,
            profesor_id,
        )
        raise HTTPException(status_code=500, detail=_ERROR_GUARDAR)

    return {"id": anotacion_id}
