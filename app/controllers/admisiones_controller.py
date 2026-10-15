"""Admisiones: aspirantes nuevos del año en preparación y su entrevista.

Ver `docs/funcionalidades/ENTREVISTA_ADMISION.md`: paso E2 (registrar,
listar, ver, editar y borrar), paso E3 (resultado y matricular) y paso E10
(las preguntas del anexo y su lectura desde la ficha del estudiante).

Reglas:

- Se consulta cualquier año; solo se registra, edita o borra en un año en
  `preparacion` (las admisiones viven en la preparación del año, decisión 1).
- Una admisión matriculada (con `estudiante_id`) es de solo consulta.
- El curso, si se elige, es un curso activo del año de la admisión.
- Un documento no se repite entre los aspirantes de un año. Si ya es de un
  estudiante del colegio, se avisa pero se registra: al matricularlo se usa
  ese mismo estudiante (decisión 11, paso E3).
- Solo se matricula un aprobado, una vez, en una sola transacción: ficha,
  matrícula, copia de lo que pasó a la entrevista y enlace.

Los mensajes de los errores son constantes escritas aquí, nunca texto de
PostgreSQL: las rutas los muestran con `str(exc)`.
"""
from psycopg2 import IntegrityError

from app.controllers.anios_lectivos_controller import (
    matricular_aspirante_en_preparacion,
)
from app.core import cuestionario_admision
from app.database import get_cursor
from app.repositories import admisiones_repository, anios_lectivos_repository
from app.services.anio_lectivo import exigir_anio_lectivo


INDICE_DOCUMENTO_POR_ANIO = "idx_admisiones_documento_por_anio"

MENSAJE_ADMISION_INEXISTENTE = "La admisión no existe."
MENSAJE_ADMISION_MATRICULADA = "Esta admisión ya está matriculada. Solo se puede consultar."
MENSAJE_NO_APROBADA = "Solo se puede matricular a un aspirante aprobado."
MENSAJE_MATRICULA_INCOMPLETA = (
    "No se pudo enlazar la admisión con el estudiante. Nada cambió."
)
MENSAJE_ENLAZADO_A_OTRA = (
    "Este estudiante ya está enlazado a la admisión de otro año. Por ahora un "
    "estudiante solo puede enlazarse a una admisión."
)


class AdmisionNoEncontradaError(Exception):
    """La admisión pedida no existe."""


class AnioNoEnPreparacionError(Exception):
    """El año de la admisión no está en preparación: solo se consulta."""


class AdmisionMatriculadaError(Exception):
    """La admisión ya tiene estudiante: solo se consulta."""


class CursoAdmisionInvalidoError(Exception):
    """El curso no es un curso activo del año de la admisión."""


class DocumentoAdmisionRepetidoError(Exception):
    """Otro aspirante del mismo año ya tiene ese documento."""


class AdmisionNoAprobadaError(Exception):
    """Se quiso matricular una admisión pendiente o no aprobada."""


class AdmisionMatriculaConflictoError(Exception):
    """La matrícula chocó con algo guardado a la vez; nada cambió."""


def _exigir_preparacion(anio, estado):
    if estado != "preparacion":
        raise AnioNoEnPreparacionError(
            f"El año lectivo {anio} no está en preparación. Las admisiones solo "
            "se registran o cambian mientras el año está en preparación."
        )


def _exigir_curso_del_anio(cursor, curso_id, anio_lectivo_id, anio):
    if curso_id is None:
        return
    curso = anios_lectivos_repository.leer_curso_para_matricula(cursor, curso_id)
    if curso is None or curso["anio_lectivo_id"] != anio_lectivo_id:
        raise CursoAdmisionInvalidoError(
            f"El curso elegido no es un curso activo del año {anio}."
        )


def _mensaje_documento_repetido(documento, anio):
    return f"Ya hay un aspirante con el documento {documento} en {anio}."


def _exigir_documento_libre(cursor, anio_lectivo_id, anio, documento, excluir_id=None):
    if documento is None:
        return
    repetida = admisiones_repository.buscar_admision_con_documento(
        cursor, anio_lectivo_id, documento, excluir_id=excluir_id
    )
    if repetida is not None:
        raise DocumentoAdmisionRepetidoError(_mensaje_documento_repetido(documento, anio))


def _regla_violada(exc):
    return getattr(getattr(exc, "diag", None), "constraint_name", None)


def _es_documento_repetido(exc):
    # Dos altas a la vez con el mismo documento pasan la comprobación previa;
    # el índice único frena la segunda y aquí se le pone el mismo mensaje.
    return _regla_violada(exc) == INDICE_DOCUMENTO_POR_ANIO


def _aviso_documento(cursor, fila):
    documento = fila["documento_identidad"]
    if documento is None:
        return None
    # Una matriculada comparte documento con su propio estudiante: no es aviso.
    estudiante = admisiones_repository.buscar_estudiante_con_documento(
        cursor, documento, excluir_id=fila["estudiante_id"]
    )
    if estudiante is None:
        return None
    nombre = " ".join(
        parte for parte in (estudiante["nombre"], estudiante["apellido"]) if parte
    )
    estado = estudiante["estado"] or "activo"
    return {
        "estudiante_id": estudiante["id"],
        "nombre": estudiante["nombre"],
        "apellido": estudiante["apellido"],
        "estado": estado,
        "mensaje": (
            f"El documento {documento} ya es de un estudiante del colegio: "
            f"{nombre} ({estado}). Al matricular, chocaría con ese estudiante."
        ),
    }


def _detalle(cursor, fila):
    matriculada = fila["estudiante_id"] is not None
    return {
        **fila,
        "matriculada": matriculada,
        "editable": fila["estado_anio"] == "preparacion" and not matriculada,
        "aviso_documento": _aviso_documento(cursor, fila),
    }


def _leer_admision(cursor, admision_id, bloquear=False):
    fila = admisiones_repository.leer_admision(cursor, admision_id, bloquear=bloquear)
    if fila is None:
        raise AdmisionNoEncontradaError(MENSAJE_ADMISION_INEXISTENTE)
    return fila


def _exigir_admision_editable(fila):
    if fila["estudiante_id"] is not None:
        raise AdmisionMatriculadaError(MENSAJE_ADMISION_MATRICULADA)
    _exigir_preparacion(fila["anio"], fila["estado_anio"])


def listar_admisiones_controller(anio_lectivo_id, resultado=None):
    """Las admisiones de un año, con los conteos de todo el año."""
    with get_cursor() as cursor:
        anio_id, anio, estado = exigir_anio_lectivo(cursor, anio_lectivo_id)
        conteos = admisiones_repository.contar_admisiones(cursor, anio_id)
        filas = admisiones_repository.listar_admisiones(cursor, anio_id, resultado)

    return {
        "anio_lectivo": {"id": anio_id, "anio": anio, "estado": estado},
        "editable": estado == "preparacion",
        "conteos": conteos,
        "admisiones": [
            {**fila, "matriculada": fila["estudiante_id"] is not None} for fila in filas
        ],
    }


def obtener_admision_controller(admision_id):
    """Una admisión completa, con el aviso si su documento ya es de un estudiante."""
    with get_cursor() as cursor:
        detalle = _detalle(cursor, _leer_admision(cursor, admision_id))
    return detalle


def obtener_cuestionario_controller():
    """Las preguntas del anexo, para que el frontend arme el formulario (E10).

    No lee la base: la lista vive en `app/core/cuestionario_admision.py`.
    """
    return cuestionario_admision.catalogo()


def obtener_admision_de_estudiante_controller(estudiante_id):
    """Las respuestas de la admisión de un estudiante, para su ficha (E10).

    Un estudiante sin admisión (los de antes, o quien llegó a mitad de año)
    responde vacío, no un error: la ficha dice "Sin entrevista de admisión".
    """
    with get_cursor() as cursor:
        admision = admisiones_repository.leer_admision_de_estudiante(cursor, estudiante_id)
    if admision is None:
        return {"admision_id": None, "anio": None, "fecha_entrevista": None, "cuestionario": {}}
    return admision


def registrar_admision_controller(anio_lectivo_id, datos):
    """Registra al aspirante en el año en preparación. Queda `pendiente`."""
    valores = datos.model_dump()
    with get_cursor(commit=True) as cursor:
        anio_id, anio, estado = exigir_anio_lectivo(cursor, anio_lectivo_id)
        _exigir_preparacion(anio, estado)
        _exigir_curso_del_anio(cursor, valores["curso_id"], anio_id, anio)
        _exigir_documento_libre(cursor, anio_id, anio, valores["documento_identidad"])
        try:
            admision_id = admisiones_repository.insertar_admision(cursor, anio_id, valores)
        except IntegrityError as exc:
            if _es_documento_repetido(exc):
                raise DocumentoAdmisionRepetidoError(
                    _mensaje_documento_repetido(valores["documento_identidad"], anio)
                ) from exc
            raise
        detalle = _detalle(cursor, _leer_admision(cursor, admision_id))
    return detalle


def actualizar_admision_controller(admision_id, datos):
    """Reemplaza datos del aspirante y de la entrevista. No cambia el resultado."""
    valores = datos.model_dump()
    with get_cursor(commit=True) as cursor:
        fila = _leer_admision(cursor, admision_id, bloquear=True)
        _exigir_admision_editable(fila)
        anio_id, anio = fila["anio_lectivo_id"], fila["anio"]
        _exigir_curso_del_anio(cursor, valores["curso_id"], anio_id, anio)
        _exigir_documento_libre(
            cursor, anio_id, anio, valores["documento_identidad"], excluir_id=admision_id
        )
        try:
            actualizadas = admisiones_repository.actualizar_admision(
                cursor, admision_id, valores
            )
        except IntegrityError as exc:
            if _es_documento_repetido(exc):
                raise DocumentoAdmisionRepetidoError(
                    _mensaje_documento_repetido(valores["documento_identidad"], anio)
                ) from exc
            raise
        if actualizadas != 1:
            # La fila está bloqueada, así que no debería pasar; si pasa, se
            # deshace todo en vez de responder como si se hubiera guardado.
            raise AdmisionMatriculadaError(MENSAJE_ADMISION_MATRICULADA)
        detalle = _detalle(cursor, _leer_admision(cursor, admision_id))
    return detalle


def borrar_admision_controller(admision_id):
    """Borra una admisión no matriculada (un error, o la familia retira sus datos)."""
    with get_cursor(commit=True) as cursor:
        fila = _leer_admision(cursor, admision_id, bloquear=True)
        _exigir_admision_editable(fila)
        if admisiones_repository.borrar_admision(cursor, admision_id) != 1:
            raise AdmisionMatriculadaError(MENSAJE_ADMISION_MATRICULADA)
    return {"mensaje": "Admisión borrada", "id": admision_id}


def cambiar_resultado_controller(admision_id, datos):
    """Guarda el resultado de la entrevista (paso E3). No aprobado exige motivo."""
    with get_cursor(commit=True) as cursor:
        fila = _leer_admision(cursor, admision_id, bloquear=True)
        _exigir_admision_editable(fila)
        cambiadas = admisiones_repository.guardar_resultado(
            cursor, admision_id, datos.resultado, datos.motivo_resultado
        )
        if cambiadas != 1:
            raise AdmisionMatriculadaError(MENSAJE_ADMISION_MATRICULADA)
        detalle = _detalle(cursor, _leer_admision(cursor, admision_id))
    return detalle


def _conflicto_de_matricula(exc, est, anio):
    """El mensaje de un choque con algo guardado a la vez, o `None` si es otro error."""
    regla = _regla_violada(exc)
    if regla == "estudiantes_documento_identidad_key":
        return AdmisionMatriculaConflictoError(
            f"Ya hay un estudiante con el documento {est.documento_identidad}. "
            "Vuelve a intentarlo."
        )
    if regla == "idx_matriculas_estudiante_anio_unico":
        return AdmisionMatriculaConflictoError(
            f"El estudiante ya tiene matrícula en {anio}."
        )
    if regla == "admisiones_estudiante_id_key":
        # La tabla admite una sola admisión por estudiante en toda su vida
        # (E1); un exalumno que entró por admisión y vuelve otro año choca.
        return AdmisionMatriculaConflictoError(MENSAJE_ENLAZADO_A_OTRA)
    return None


def matricular_admision_controller(admision_id, est):
    """Matricula a un aspirante aprobado en el año de su admisión (paso E3).

    Todo en una transacción: la ficha (nueva, o la del exalumno que vuelve) y
    su matrícula, la copia de lo que pasó a la entrevista y el enlace. Si algo
    falla, no cambia nada.
    """
    with get_cursor(commit=True) as cursor:
        fila = _leer_admision(cursor, admision_id, bloquear=True)
        if fila["estudiante_id"] is not None:
            raise AdmisionMatriculadaError(MENSAJE_ADMISION_MATRICULADA)
        if fila["resultado"] != "aprobado":
            raise AdmisionNoAprobadaError(MENSAJE_NO_APROBADA)
        try:
            matricula = matricular_aspirante_en_preparacion(
                cursor, fila["anio_lectivo_id"], est
            )
            estudiante_id = matricula["estudiante_id"]
            copiadas = admisiones_repository.copiar_datos_a_estudiante(
                cursor, admision_id, estudiante_id
            )
            enlazadas = admisiones_repository.enlazar_estudiante(
                cursor, admision_id, estudiante_id
            )
        except IntegrityError as exc:
            conflicto = _conflicto_de_matricula(exc, est, fila["anio"])
            if conflicto is None:
                raise
            raise conflicto from exc
        if copiadas != 1 or enlazadas != 1:
            raise AdmisionMatriculaConflictoError(MENSAJE_MATRICULA_INCOMPLETA)
        detalle = _detalle(cursor, _leer_admision(cursor, admision_id))

    nombre = " ".join(parte for parte in (est.nombre, est.apellido) if parte)
    return {
        "mensaje": f"Matrícula creada en {matricula['anio']} para {nombre}.",
        "estudiante_id": estudiante_id,
        "matricula_id": matricula["matricula_id"],
        "anio_lectivo_id": matricula["anio_lectivo_id"],
        "curso_id": matricula["curso_id"],
        "estudiante_existente": matricula["estudiante_existente"],
        "admision": detalle,
    }
