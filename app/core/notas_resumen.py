"""Las notas por periodo del resumen del estudiante (la ficha del admin).

Ver `docs/funcionalidades/NOTAS_RESUMEN_ESTUDIANTE.md`. Sin base de datos y
sin HTTP: el controlador lee la planilla del año y los porcentajes, y este
modulo arma la respuesta.

La nota de una materia en un periodo es **la del reporte parcial** (la foto de
la planilla vigente) mas las caritas de preescolar:

- sin las columnas internas (`mas_alto`, "Desde React"), como la planilla;
- primaria: el promedio de las notas de 1 a 5 (los ceros no cuentan);
- preescolar: el promedio del valor de las caritas y la carita mas cercana;
- con porcentajes activos, la ponderada de `calcular_nota_del_periodo`.

"Todo el año" es el promedio de los periodos con nota (decision 4).
"""
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from app.core.nivel_academico import resolver_tipo_evaluacion
from app.core.nota_periodo import (
    _redondear,
    admite_porcentaje,
    calcular_nota_del_periodo,
    tipo_de_evaluacion_de_celdas,
)
from app.core.subnotas_planilla import normalizar_nota
from app.core.valoraciones_desarrollo import (
    es_valoracion,
    valor_de_valoracion,
    valoracion_desde_promedio,
)


PERIODOS = (1, 2, 3, 4)


def _promedio(valores):
    """Fraccion exacta del promedio, o None sin valores."""
    if not valores:
        return None
    return sum(Fraction(valor) for valor in valores) / len(valores)


def _resultado(tipo_evaluacion, promedio):
    """`(valor, valoracion)` de un promedio exacto: dos decimales y, en
    preescolar, la carita mas cercana al promedio exacto."""
    if promedio is None:
        return None, None
    if tipo_evaluacion == "desarrollo":
        return _redondear(promedio), valoracion_desde_promedio(promedio)
    return _redondear(promedio), None


def nota_sin_porcentajes(tipo_evaluacion, celdas):
    """`(valor, valoracion)` del promedio simple de las celdas `(tipo, nota, valoracion)`."""
    valores = []
    for tipo_nota, nota, valoracion in celdas:
        if not admite_porcentaje(tipo_nota):
            continue
        if tipo_evaluacion == "desarrollo":
            if es_valoracion(valoracion):
                valores.append(valor_de_valoracion(valoracion))
        elif nota is not None:
            normalizada = normalizar_nota(nota)
            if normalizada is not None:
                valores.append(normalizada)
    return _resultado(tipo_evaluacion, _promedio(valores))


def nota_del_periodo(tipo_evaluacion, celdas, porcentajes=None):
    """La nota de una materia en un periodo; ponderada si hay porcentajes activos."""
    if porcentajes:
        return calcular_nota_del_periodo(tipo_evaluacion, celdas, porcentajes)
    return nota_sin_porcentajes(tipo_evaluacion, celdas)


def nota_del_anio(tipo_evaluacion, valores_de_los_periodos):
    """El promedio de los periodos con nota (sus valores de dos decimales)."""
    valores = [valor for valor in valores_de_los_periodos if valor is not None]
    return _resultado(tipo_evaluacion, _promedio(valores))


def _celda(valor, valoracion):
    if valor is None:
        return None
    return {"nota": float(valor), "valoracion": valoracion}


def _materias_de_las_filas(filas):
    """Agrupa las filas de la planilla del año por clase, en su orden.

    Cada fila es `(asignacion_id, materia, nivel, periodo, tipo_nota, nota,
    tipo_evaluacion, valoracion)`; una materia sin notas trae una sola fila
    con el periodo vacio.
    """
    materias = {}
    for asignacion_id, materia, nivel, periodo, tipo_nota, nota, tipo_celda, valoracion in filas:
        actual = materias.setdefault(
            asignacion_id,
            {"materia": materia, "nivel": nivel, "tipos": [], "celdas": {}},
        )
        if periodo is None:
            continue
        actual["tipos"].append(tipo_celda or "numerica")
        actual["celdas"].setdefault(periodo, []).append((tipo_nota, nota, valoracion))
    return materias


def armar_notas_por_periodo(filas, porcentajes_por_clase_y_periodo=None):
    """`{"materias": [...], "promedio": {...}}` para la respuesta.

    `porcentajes_por_clase_y_periodo` va de `(asignacion_id, periodo)` a los
    porcentajes activos de esa clase en ese periodo.
    """
    porcentajes = porcentajes_por_clase_y_periodo or {}
    materias = []
    numericas_por_periodo = {periodo: [] for periodo in PERIODOS}
    numericas_del_anio = []

    for asignacion_id, materia in _materias_de_las_filas(filas).items():
        tipo = resolver_tipo_evaluacion(
            materia["nivel"], tipo_de_evaluacion_de_celdas(materia["tipos"])
        )
        periodos = {}
        valores = []
        for periodo in PERIODOS:
            valor, valoracion = nota_del_periodo(
                tipo,
                materia["celdas"].get(periodo, []),
                porcentajes.get((asignacion_id, periodo)),
            )
            periodos[str(periodo)] = _celda(valor, valoracion)
            valores.append(valor)
            if tipo != "desarrollo" and valor is not None:
                numericas_por_periodo[periodo].append(valor)

        valor_anio, valoracion_anio = nota_del_anio(tipo, valores)
        if tipo != "desarrollo" and valor_anio is not None:
            numericas_del_anio.append(valor_anio)
        materias.append({
            "materia": materia["materia"],
            "tipo_evaluacion": tipo,
            "periodos": periodos,
            "anio": _celda(valor_anio, valoracion_anio),
        })

    promedio = {
        str(periodo): _promedio_general(numericas_por_periodo[periodo]) for periodo in PERIODOS
    }
    promedio["anio"] = _promedio_general(numericas_del_anio)
    return {"materias": materias, "promedio": promedio}


def _promedio_general(valores):
    promedio = _promedio(valores)
    return None if promedio is None else float(_redondear(promedio))


def notas_por_periodo_vacias():
    """La forma de la respuesta sin ninguna materia."""
    return armar_notas_por_periodo([])


def notas_compatibles(resumen):
    """`(notas, promedio_general)` con la forma vieja, desde "Todo el año".

    Para el frontend que todavia no lee `notas_por_periodo`: solo las materias
    numericas con nota, a un decimal, y el promedio general a un decimal.
    """
    notas = [
        {"materia": materia["materia"], "promedio": _un_decimal(materia["anio"]["nota"])}
        for materia in resumen["materias"]
        if materia["tipo_evaluacion"] != "desarrollo" and materia["anio"] is not None
    ]
    promedio_anio = resumen["promedio"]["anio"]
    return notas, (0.0 if promedio_anio is None else _un_decimal(promedio_anio))


def _un_decimal(valor):
    """Un decimal, mitad hacia arriba, como el `ROUND(..., 1)` de antes."""
    return float(Decimal(str(valor)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def inasistencias_por_periodo(fila):
    """`{"1": .., "2": .., "3": .., "4": .., "anio": ..}` desde la fila de conteos.

    `fila` es `(periodo_1, periodo_2, periodo_3, periodo_4, total)`. El total
    cuenta tambien las de un periodo raro: es el mismo numero de antes.
    """
    conteos = tuple(fila) if fila else (0, 0, 0, 0, 0)
    respuesta = {str(periodo): int(conteos[indice] or 0) for indice, periodo in enumerate(PERIODOS)}
    respuesta["anio"] = int(conteos[len(PERIODOS)] or 0)
    return respuesta
