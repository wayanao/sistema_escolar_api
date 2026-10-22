"""Reglas de los porcentajes por tipo de nota. Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`.

Parte B, PB2, PB3 y PB8. Igual que en las subnotas, sus errores propios son
excepciones con mensaje **constante** y la ruta las traduce a 404 o 422; las
guardias compartidas (permiso de la asignacion y año lectivo) ya son
`HTTPException` y llegan a la respuesta tal cual.

`guardar_porcentaje_controller` abre una sola conexion y comprueba y escribe en
la misma transaccion. Consultas, para un profesor (el admin hace una menos: su
permiso no consulta nada): 7 -permiso, año, asignacion academica, bloquear la
clase, los tipos de la planilla, sus porcentajes y la escritura-. **No crece
con el numero de estudiantes ni de tipos.**

Lo que es valido o no, cuanto suman y si estan activos lo decide
`app/core/nota_periodo.py`; este modulo lee, llama y escribe.
"""
from app.core.nota_periodo import (
    SUMA_COMPLETA,
    admite_porcentaje,
    es_porcentaje_valido,
    porcentajes_activos,
    suma_de_porcentajes,
)
from app.core.permissions import require_asignacion_access
from app.core.subnotas_planilla import clave_de_tipo
from app.database import get_cursor
from app.repositories import porcentajes_planilla_repository as repositorio
from app.services.anio_lectivo import exigir_asignacion_editable
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor


TIPO_NO_ENCONTRADO = "Ese tipo de nota no existe en esta planilla."
TIPO_SIN_PORCENTAJE = "Ese tipo de nota no lleva porcentaje."
PORCENTAJE_INVALIDO = "El porcentaje debe ser un número entero de 1 a 100."
SUMA_EXCEDIDA = "Los porcentajes de esta planilla no pueden sumar más de 100 %."


class ErrorDePorcentajes(Exception):
    """Base de los errores propios. La ruta decide el codigo HTTP de cada uno."""


class TipoNoEncontradoError(ErrorDePorcentajes):
    """El tipo de nota no esta en la planilla. La ruta lo traduce a 404."""


class TipoSinPorcentajeError(ErrorDePorcentajes):
    """Columna interna que no se muestra. La ruta lo traduce a 422."""


class PorcentajeInvalidoError(ErrorDePorcentajes):
    """No es un entero de 1 a 100 (PB2). La ruta lo traduce a 422."""


class SumaExcedidaError(ErrorDePorcentajes):
    """Con ese porcentaje la clase pasaria de 100 (PB3). La ruta lo traduce a 422."""


def _columna_del_tipo(tipos, tipo_nota):
    """El nombre del tipo tal como esta en la planilla, o None si no esta."""
    clave = clave_de_tipo(tipo_nota)
    for tipo in tipos:
        if clave_de_tipo(tipo) == clave:
            return tipo.strip()
    return None


def guardar_porcentaje_controller(datos, *, usuario):
    """Guarda, cambia o quita (`porcentaje` en `null`) el porcentaje de un tipo.

    Lo que no depende de la base se rechaza antes de abrirla: la columna
    interna y el porcentaje que no es un entero de 1 a 100. La suma se mira
    con la clase bloqueada, sin contar el porcentaje que el tipo tenia, y el
    de un tipo que ya no esta en la planilla no cuenta.

    Devuelve el tipo con el nombre de su columna, el porcentaje guardado, la
    suma de la clase y si los porcentajes quedaron activos (QB2).
    """
    if not admite_porcentaje(datos.tipo_nota):
        raise TipoSinPorcentajeError(TIPO_SIN_PORCENTAJE)
    if datos.porcentaje is not None and not es_porcentaje_valido(datos.porcentaje):
        raise PorcentajeInvalidoError(PORCENTAJE_INVALIDO)

    with get_cursor(commit=True) as cursor:
        require_asignacion_access(datos.asignacion_id, usuario, cursor=cursor)
        exigir_asignacion_editable(cursor, datos.asignacion_id, usuario)
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, datos.asignacion_id)

        repositorio.bloquear_clase(cursor, asignacion_id)
        tipos = repositorio.leer_tipos_de_planilla(cursor, asignacion_id, datos.periodo)
        tipo_nota = _columna_del_tipo(tipos, datos.tipo_nota)
        if tipo_nota is None:
            raise TipoNoEncontradoError(TIPO_NO_ENCONTRADO)

        porcentajes = {
            tipo: porcentaje
            for tipo, porcentaje in repositorio.leer_porcentajes_de_planilla(
                cursor, asignacion_id, datos.periodo
            )
            if clave_de_tipo(tipo) != clave_de_tipo(tipo_nota)
        }

        if datos.porcentaje is None:
            repositorio.quitar_porcentaje(cursor, asignacion_id, datos.periodo, tipo_nota)
        else:
            if suma_de_porcentajes(tipos, porcentajes) + datos.porcentaje > SUMA_COMPLETA:
                raise SumaExcedidaError(SUMA_EXCEDIDA)
            repositorio.guardar_porcentaje(
                cursor, asignacion_id, datos.periodo, tipo_nota, datos.porcentaje
            )
            porcentajes[tipo_nota] = datos.porcentaje

    return {
        "tipo_nota": tipo_nota,
        "porcentaje": datos.porcentaje,
        "suma": suma_de_porcentajes(tipos, porcentajes),
        "activos": porcentajes_activos(tipos, porcentajes),
    }
