"""Bitacora del observador del estudiante.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Leer, crear y editar.
**`DELETE` no existe y no debe anadirse**: nadie borra una anotacion, es el
invariante 1 del documento. Hay prueba que lo impide.

Tambien la firma del acudiente en cada anotacion
(`docs/funcionalidades/FIRMA_OBSERVADOR.md`): tomarla, leerla para imprimir y
sugerir al padre y a la madre. Una firma tampoco se edita ni se borra.

Convive con `app/routes/observaciones.py`, que sirve la pantalla vieja. Esa
sigue funcionando y no se toca hasta que esta este verificada.
"""
import base64
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.errors import UniqueViolation

from app.core.firma_observador import (
    PREFIJO_DATA_URL,
    calcular_huella,
    decodificar_imagen,
    enmascarar_documento,
    huella_coincide,
    puede_tomar_firma,
    sha256_de_imagen,
    version_de_anotacion,
)
from app.core.permissions import require_estudiante_access
from app.database import get_cursor
from app.dependencies import get_current_user
from app.repositories import observador_repository
from app.schemas.observador import AnotacionCreate, AnotacionUpdate, FirmaAnotacionCreate
from app.services.anio_lectivo import (
    AnioLectivoInexistenteError,
    AnioLectivoNoPermitidoError,
    anio_distinto_del_activo,
    exigir_anio_editable,
    exigir_anotacion_editable,
    puede_guardar_en_anio,
)

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
_ERROR_FIRMAR = "No se pudo guardar la firma. Intenta de nuevo."
_ERROR_CONSULTAR_FIRMAS = "No se pudieron consultar las firmas. Intenta de nuevo."
_ERROR_YA_FIRMADA = "Esta anotacion ya tiene la firma del acudiente."
_ERROR_CAMBIO_AL_FIRMAR = (
    "La anotacion cambio mientras se firmaba. Vuelve a abrirla y pide la firma otra vez."
)
_ERROR_SIN_PERMISO_FIRMA = (
    "Solo el autor, el director de grupo o el admin pueden tomar esta firma."
)
_ERROR_FIRMADA_NO_SE_EDITA = (
    "Esta anotacion ya tiene la firma del acudiente y no se puede editar. "
    "Escribe una anotacion nueva para aclararla."
)

router = APIRouter(tags=["Observador"], dependencies=[Depends(get_current_user)])


def _datos_de_firma(
    firmante_nombre,
    firmante_tipo_documento,
    firmante_documento,
    firmante_parentesco,
    tomada_por_profesor_id,
    tomada_por_usuario_id,
    tomada_por_nombre,
    firmada_en,
):
    """Lo que la huella cubre de una firma, con los nombres de
    `CAMPOS_DE_LA_FIRMA`."""
    return {
        "firmante_nombre": firmante_nombre,
        "firmante_tipo_documento": firmante_tipo_documento,
        "firmante_documento": firmante_documento,
        "firmante_parentesco": firmante_parentesco,
        "tomada_por_profesor_id": tomada_por_profesor_id,
        "tomada_por_usuario_id": tomada_por_usuario_id,
        "tomada_por_nombre": tomada_por_nombre,
        "firmada_en": firmada_en,
    }


def _anotacion(fila, usuario, estudiante_id):
    """Una fila de la consulta, con la forma que consume el frontend.

    `profesor_id` viaja para que la pantalla decida si pinta el boton Editar.
    Es **comodidad visual**: la regla de verdad la impone el servidor, y el
    frontend no puede ser la unica defensa.

    `positiva` sigue viajando aunque desde el 2026-09-09 nadie la rellene ni la
    muestre, igual que `materia`. La columna no se borra y la forma de la
    respuesta no cambia: si algun dia vuelve la marca, solo cambia la pantalla.

    Firma del acudiente (`docs/funcionalidades/FIRMA_OBSERVADOR.md`): `version`,
    `puede_firmar` y `firma`. Como `profesor_id` para Editar, `puede_firmar` es
    comodidad visual: dice de antemano si el boton va a funcionar, con las
    mismas reglas que aplica la firma, y la pantalla no tiene como saber quien
    es el director de grupo. `firma` lleva el documento **enmascarado**: la
    bitacora la ven todos los profesores del alumno.
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
        director_grupo_id,
        anio,
        estado_anio,
        firmante_nombre,
        firmante_tipo_documento,
        firmante_documento,
        firmante_parentesco,
        tomada_por_profesor_id,
        tomada_por_usuario_id,
        tomada_por_nombre,
        firmada_en,
        huella,
        imagen_sha256,
    ) = fila

    # Lo que cubren la version y la huella. El `estudiante_id` no viaja en la
    # fila: es el de la ruta, el unico que la consulta deja pasar.
    contenido = {
        "id": anotacion_id,
        "estudiante_id": estudiante_id,
        "profesor_id": profesor_id,
        "periodo": periodo,
        "conductual": conductual,
        "cognitivo": cognitivo,
        "lenguaje": lenguaje,
        "creada_en": creada_en,
        "editada_en": editada_en,
    }

    firma = None
    if huella is not None:
        datos = _datos_de_firma(
            firmante_nombre,
            firmante_tipo_documento,
            firmante_documento,
            firmante_parentesco,
            tomada_por_profesor_id,
            tomada_por_usuario_id,
            tomada_por_nombre,
            firmada_en,
        )
        firma = {
            "firmante_nombre": firmante_nombre,
            "firmante_tipo_documento": firmante_tipo_documento,
            "firmante_documento_enmascarado": enmascarar_documento(firmante_documento),
            "firmante_parentesco": firmante_parentesco,
            "firmada_en": firmada_en,
            "tomada_por_nombre": tomada_por_nombre,
            "integra": huella_coincide(contenido, datos, imagen_sha256, huella),
        }

    anio_y_estado = (anio, estado_anio) if anio is not None else None
    puede_firmar = (
        firma is None
        and puede_guardar_en_anio(anio_y_estado, usuario)
        and puede_tomar_firma(usuario, profesor_id, director_grupo_id)
    )

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
        "version": version_de_anotacion(contenido),
        "puede_firmar": puede_firmar,
        "firma": firma,
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
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
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

    Año lectivo (fase 3, paso 3.5b): las anotaciones son las del año activo,
    o las de `?anio_lectivo_id=` si lo pide el admin. Un profesor que pide otro
    año recibe 403 (decision 4); un año que no existe, 404.

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
            anio = anio_distinto_del_activo(cursor, anio_lectivo_id, current_user)
            filas = observador_repository.leer_bitacora(
                cursor, estudiante_id, periodo, anio_lectivo_id=anio
            )

            # Sin filas el estudiante no existe. Uno real sin anotaciones trae
            # una fila de relleno, con el nivel y el resto en NULL.
            if not filas:
                raise HTTPException(status_code=404, detail=_ERROR_NO_EXISTE)
    except HTTPException:
        raise
    # Sus mensajes son constantes de app/services/anio_lectivo.py, no texto de
    # PostgreSQL: se pueden mostrar.
    except AnioLectivoInexistenteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AnioLectivoNoPermitidoError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
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
        "anotaciones": [
            _anotacion(fila, current_user, estudiante_id)
            for fila in filas
            if fila[1] is not None
        ],
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
            # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
            exigir_anotacion_editable(cursor, anotacion_id, current_user)
            # Firma del acudiente: lo firmado no se edita, por nadie
            # (FIRMA_OBSERVADOR.md, invariante 2). Bloquea la anotacion antes de
            # mirar, para no cruzarse con una firma que se este guardando.
            if observador_repository.bloquear_y_saber_si_esta_firmada(cursor, anotacion_id):
                raise HTTPException(status_code=409, detail=_ERROR_FIRMADA_NO_SE_EDITA)
            actualizada = observador_repository.actualizar_anotacion_del_autor(
                cursor,
                anotacion_id,
                profesor_id,
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


# ---------------------------------------------------------------------------
# Firma del acudiente. Ver docs/funcionalidades/FIRMA_OBSERVADOR.md.
#
# En los errores de estas rutas se registra **solo el tipo** de la excepcion,
# nunca su mensaje: el de PostgreSQL puede traer la fila entera ("Failing row
# contains ..."), con el documento del acudiente y la imagen de su firma. Es el
# invariante 6.
# ---------------------------------------------------------------------------


@router.post("/observador/anotaciones/{anotacion_id}/firma", status_code=201)
def firmar_anotacion(
    anotacion_id: int,
    data: FirmaAnotacionCreate,
    current_user: dict = Depends(get_current_user),
):
    """El acudiente firma, en pantalla, una anotacion que acaba de leer.

    La toman el autor, el director de grupo del alumno o el admin
    (decision 3). Quien la toma, la fecha y la hora salen del token y del
    servidor, nunca del cuerpo (invariante 4). Firmar sigue la misma regla de
    año que editar: el profesor, solo en el año activo; nadie, en uno cerrado.

    Errores: 404 si la anotacion no existe; 403 sin permiso o fuera de su año;
    409 si ya esta firmada, si cambio desde que se mostro o si el año esta
    cerrado; 422 si los datos o la imagen no sirven.
    """
    rol = current_user.get("rol")
    if rol not in ("profesor", "admin"):
        raise HTTPException(status_code=403, detail=_ERROR_SIN_PERMISO_FIRMA)

    # Profesores y admins viven en tablas distintas: el id va a la columna de
    # su tabla y la otra queda en NULL, como exige el CHECK de la migracion.
    profesor_id = current_user["id"] if rol == "profesor" else None
    usuario_id = current_user["id"] if rol == "admin" else None
    # El esquema ya la valido: aqui solo se pasa a bytes.
    imagen = decodificar_imagen(data.imagen)

    try:
        with get_cursor(commit=True) as cursor:
            leida = observador_repository.leer_anotacion_para_firmar(
                cursor, anotacion_id, profesor_id, usuario_id
            )
            if leida is None:
                raise HTTPException(status_code=404, detail=_ERROR_ANOTACION_NO_EXISTE)
            anotacion = leida["anotacion"]

            require_estudiante_access(anotacion["estudiante_id"], current_user, cursor=cursor)
            exigir_anio_editable(leida["anio_y_estado"], current_user)
            if not puede_tomar_firma(
                current_user, anotacion["profesor_id"], leida["director_grupo_id"]
            ):
                raise HTTPException(status_code=403, detail=_ERROR_SIN_PERMISO_FIRMA)
            if leida["firmada"]:
                raise HTTPException(status_code=409, detail=_ERROR_YA_FIRMADA)
            if version_de_anotacion(anotacion) != data.version:
                raise HTTPException(status_code=409, detail=_ERROR_CAMBIO_AL_FIRMAR)

            firma = _datos_de_firma(
                data.firmante_nombre,
                data.firmante_tipo_documento,
                data.firmante_documento,
                data.firmante_parentesco,
                profesor_id,
                usuario_id,
                leida["tomada_por_nombre"],
                leida["ahora"],
            )
            huella = calcular_huella(anotacion, firma, sha256_de_imagen(imagen))
            firma_id = observador_repository.crear_firma(
                cursor, anotacion_id, firma, imagen, huella
            )
    except HTTPException:
        raise
    except UniqueViolation:
        # Otra firma de la misma anotacion se guardo mientras tanto: el UNIQUE
        # de la tabla es la ultima defensa del invariante 1.
        raise HTTPException(status_code=409, detail=_ERROR_YA_FIRMADA)
    except Exception as exc:
        logger.error(
            "Fallo al firmar la anotacion %s (la toma %s %s): %s",
            anotacion_id,
            rol,
            current_user["id"],
            type(exc).__name__,
        )
        raise HTTPException(status_code=500, detail=_ERROR_FIRMAR)

    return {
        "id": firma_id,
        "anotacion_id": anotacion_id,
        "firmante_nombre": firma["firmante_nombre"],
        "firmante_tipo_documento": firma["firmante_tipo_documento"],
        "firmante_documento_enmascarado": enmascarar_documento(firma["firmante_documento"]),
        "firmante_parentesco": firma["firmante_parentesco"],
        "firmada_en": firma["firmada_en"],
        "tomada_por_nombre": firma["tomada_por_nombre"],
        "integra": True,
    }


def _firma_para_imprimir(fila):
    """Una fila de `leer_firmas_para_imprimir`, con la forma del impreso: el
    documento **completo** y la imagen como `data:` lista para un `<img>`."""
    (
        anotacion_id,
        estudiante_id,
        profesor_id,
        periodo,
        conductual,
        cognitivo,
        lenguaje,
        creada_en,
        editada_en,
        firmante_nombre,
        firmante_tipo_documento,
        firmante_documento,
        firmante_parentesco,
        tomada_por_profesor_id,
        tomada_por_usuario_id,
        tomada_por_nombre,
        firmada_en,
        huella,
        imagen_png,
    ) = fila

    # psycopg2 entrega `bytea` como `memoryview`.
    imagen = bytes(imagen_png)
    contenido = {
        "id": anotacion_id,
        "estudiante_id": estudiante_id,
        "profesor_id": profesor_id,
        "periodo": periodo,
        "conductual": conductual,
        "cognitivo": cognitivo,
        "lenguaje": lenguaje,
        "creada_en": creada_en,
        "editada_en": editada_en,
    }
    datos = _datos_de_firma(
        firmante_nombre,
        firmante_tipo_documento,
        firmante_documento,
        firmante_parentesco,
        tomada_por_profesor_id,
        tomada_por_usuario_id,
        tomada_por_nombre,
        firmada_en,
    )

    return {
        "anotacion_id": anotacion_id,
        "firmante_nombre": firmante_nombre,
        "firmante_tipo_documento": firmante_tipo_documento,
        "firmante_documento": firmante_documento,
        "firmante_parentesco": firmante_parentesco,
        "firmada_en": firmada_en,
        "tomada_por_nombre": tomada_por_nombre,
        "integra": huella_coincide(contenido, datos, sha256_de_imagen(imagen), huella),
        "imagen": PREFIJO_DATA_URL + base64.b64encode(imagen).decode("ascii"),
    }


@router.get("/observador/{estudiante_id}/firmas")
def obtener_firmas_para_imprimir(
    estudiante_id: int,
    periodo: int | None = Query(
        None,
        ge=1,
        le=4,
        description="El mismo filtro que la bitacora: se imprime lo que se ve.",
    ),
    current_user: dict = Depends(get_current_user),
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Las firmas, con imagen y documento completo, para imprimir el observador.

    Las mismas anotaciones que `GET /observador/{estudiante_id}` con los mismos
    filtros, y la misma puerta: quien ve la bitacora puede imprimirla. Es la
    unica lectura que trae imagenes, y solo se pide al imprimir
    (invariante 7).
    """
    try:
        with get_cursor() as cursor:
            require_estudiante_access(estudiante_id, current_user, cursor=cursor)
            anio = anio_distinto_del_activo(cursor, anio_lectivo_id, current_user)
            filas = observador_repository.leer_firmas_para_imprimir(
                cursor, estudiante_id, periodo, anio_lectivo_id=anio
            )
    except HTTPException:
        raise
    except AnioLectivoInexistenteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AnioLectivoNoPermitidoError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "Fallo al leer las firmas del estudiante %s: %s",
            estudiante_id,
            type(exc).__name__,
        )
        raise HTTPException(status_code=500, detail=_ERROR_CONSULTAR_FIRMAS)

    return [_firma_para_imprimir(fila) for fila in filas]


@router.get("/observador/{estudiante_id}/firmantes-sugeridos")
def obtener_firmantes_sugeridos(
    estudiante_id: int,
    current_user: dict = Depends(get_current_user),
):
    """El padre y la madre de la ficha, para no escribirlos a mano al firmar.

    Solo para quien puede tomar alguna firma del alumno: el admin, su director
    de grupo o un profesor que le haya escrito una anotacion este año. Los
    documentos de los padres no son para todos los profesores del curso.
    Devuelve solo los que tienen nombre, en una lista que puede quedar vacia.
    """
    rol = current_user.get("rol")
    profesor_id = current_user["id"] if rol == "profesor" else None

    try:
        with get_cursor() as cursor:
            require_estudiante_access(estudiante_id, current_user, cursor=cursor)
            fila = observador_repository.leer_firmantes_sugeridos(
                cursor, estudiante_id, profesor_id
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Fallo al leer los firmantes sugeridos del estudiante %s: %s",
            estudiante_id,
            type(exc).__name__,
        )
        raise HTTPException(status_code=500, detail=_ERROR_CONSULTAR)

    if fila is None:
        raise HTTPException(status_code=404, detail=_ERROR_NO_EXISTE)
    if rol != "admin" and not fila[6]:
        raise HTTPException(status_code=403, detail=_ERROR_SIN_PERMISO_FIRMA)

    padres = (("Padre", fila[0], fila[1], fila[2]), ("Madre", fila[3], fila[4], fila[5]))
    return [
        {
            "parentesco": parentesco,
            "nombre": nombre.strip(),
            "tipo_documento": (tipo_documento or "").strip(),
            "documento": (documento or "").strip(),
        }
        for parentesco, nombre, tipo_documento, documento in padres
        if nombre and nombre.strip()
    ]
