"""La nota de un periodo con porcentajes por tipo de nota (parte B).

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, "Propuestas de B0": PB2 a
PB4, QB1 y QB2. Es **el unico lugar** donde se calcula la nota ponderada: la
planilla, el boletin, el reporte parcial y los rankings la piden aqui cuando
los porcentajes de esa clase y periodo estan activos. Sin porcentajes activos
nadie llama a este modulo y cada lugar conserva su formula de hoy (QB4).

El frontend tiene la gemela para la vista previa. **Lo que se guarda es lo que
calcula este modulo.**

Sin base de datos y sin HTTP. Una celda se representa como
`(tipo_nota, nota, valoracion)`: la nota (primaria) o el codigo de la carita
(preescolar), y el otro en `None`.
"""
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from app.core.subnotas_planilla import admite_subnotas, clave_de_tipo, normalizar_nota
from app.core.valoraciones_desarrollo import (
    es_valoracion,
    valor_de_valoracion,
    valoracion_desde_promedio,
)


PORCENTAJE_MINIMO = 1
PORCENTAJE_MAXIMO = 100
"""PB2: porcentajes enteros de 1 a 100."""

SUMA_COMPLETA = 100
"""QB2: los porcentajes cuentan solo cuando suman exactamente esto."""

_CENTESIMA = Decimal("0.01")


def admite_porcentaje(tipo_nota):
    """False para las columnas internas (`mas_alto`, "Desde React").

    Son las mismas que no admiten subnotas (P11): la planilla no las muestra,
    asi que no llevan porcentaje ni cuentan para completar los 100.
    """
    return admite_subnotas(tipo_nota)


def es_porcentaje_valido(valor):
    """True solo para un entero de 1 a 100 (PB2). Un booleano no es entero."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return False
    return PORCENTAJE_MINIMO <= valor <= PORCENTAJE_MAXIMO


def _porcentajes_por_clave(porcentajes):
    return {clave_de_tipo(tipo): valor for tipo, valor in porcentajes.items()}


def _claves_visibles(tipos):
    return {clave_de_tipo(tipo) for tipo in tipos if admite_porcentaje(tipo)}


def suma_de_porcentajes(tipos, porcentajes):
    """Suma de los porcentajes de los tipos que estan en la planilla.

    El de un tipo que ya no existe no cuenta. Los tipos se comparan sin
    mayusculas ni espacios en los extremos, como `LOWER(TRIM(...))`.
    """
    por_clave = _porcentajes_por_clave(porcentajes)
    return sum(por_clave[clave] for clave in _claves_visibles(tipos) if clave in por_clave)


def porcentajes_activos(tipos, porcentajes):
    """QB2, todo o nada: cada tipo visible tiene su porcentaje y suman 100.

    Sin tipos visibles no estan activos: no hay nada que ponderar.
    """
    claves = _claves_visibles(tipos)
    por_clave = _porcentajes_por_clave(porcentajes)
    if not claves or not claves.issubset(por_clave):
        return False
    return suma_de_porcentajes(tipos, porcentajes) == SUMA_COMPLETA


def _redondear(fraccion):
    """Dos decimales, mitad hacia arriba (P7), desde la fraccion exacta."""
    exacto = Decimal(fraccion.numerator) / Decimal(fraccion.denominator)
    return exacto.quantize(_CENTESIMA, rounding=ROUND_HALF_UP)


def _promedio_ponderado(valores_y_pesos):
    """Fraccion exacta de suma(valor x peso) / suma(pesos), o None si no hay."""
    if not valores_y_pesos:
        return None
    total = sum(Fraction(valor) * peso for valor, peso in valores_y_pesos)
    return total / sum(peso for _, peso in valores_y_pesos)


def calcular_nota_del_periodo(tipo_evaluacion, celdas, porcentajes):
    """`(valor, valoracion)` de la nota ponderada de un estudiante (PB4).

    - Solo pesan las celdas con valor de un tipo con porcentaje. Una celda
      vacia no cuenta y su peso se reparte entre las demas, como hoy no cuenta
      una celda vacia en el promedio.
    - Primaria: `valor` es la nota con dos decimales, mitad hacia arriba, y
      `valoracion` es `None`. Una nota fuera de 1 a 5 (datos viejos) no
      cuenta, igual que el boletin y el reporte parcial de hoy descartan los
      ceros.
    - Preescolar (QB1): las caritas se pasan a numero con la escala de
      siempre; `valor` es ese promedio con dos decimales (lo que se guarda
      como definitiva) y `valoracion` la carita mas cercana al promedio
      exacto, con empate hacia la mas alta (P8).
    - Sin ninguna celda que cuente devuelve `(None, None)`.
    """
    por_clave = _porcentajes_por_clave(porcentajes)
    valores_y_pesos = []
    for tipo_nota, nota, valoracion in celdas:
        peso = por_clave.get(clave_de_tipo(tipo_nota))
        if not peso or not admite_porcentaje(tipo_nota):
            continue
        if tipo_evaluacion == "desarrollo":
            if es_valoracion(valoracion):
                valores_y_pesos.append((valor_de_valoracion(valoracion), peso))
        elif nota is not None:
            normalizada = normalizar_nota(nota)
            if normalizada is not None:
                valores_y_pesos.append((normalizada, peso))

    promedio = _promedio_ponderado(valores_y_pesos)
    if promedio is None:
        return None, None
    if tipo_evaluacion == "desarrollo":
        return _redondear(promedio), valoracion_desde_promedio(promedio)
    return _redondear(promedio), None
