"""Reglas puras de las subnotas de la planilla.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`. Aqui vive el calculo de la
celda a partir de sus subnotas (P2, P7 y P8) y el armado de las subnotas en la
respuesta de la planilla. Sin base de datos y sin HTTP: los controladores leen,
llaman a estas funciones y escriben.

El frontend tiene la misma formula en `src/utils/planilla/subnotas.js` para la
vista previa del modal. **Lo que se guarda es lo que calcula este modulo.**

Una calificacion se representa como el par `(nota, valoracion)` de su fila:
una nota (primaria) o un codigo de carita (preescolar), y el otro en `None`.
"""
import math
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from app.core.valoraciones_desarrollo import (
    es_valoracion,
    valor_de_valoracion,
    valoracion_desde_promedio,
)


MAXIMO_SUBNOTAS_POR_TIPO = 20
"""P11: hasta 20 subnotas por tipo de nota."""

# Columnas que existen en notas_detalle pero no se ven como tipo de nota: la
# planilla descarta "Desde React" y el frontend oculta "mas_alto". No admiten
# subnotas porque nadie podria verlas.
_TIPOS_SIN_SUBNOTAS = frozenset({"mas_alto", "desde react"})

_CENTESIMA = Decimal("0.01")


def clave_de_tipo(tipo_nota):
    """Como se comparan los tipos de nota: igual que `LOWER(TRIM(...))` en SQL."""
    return (tipo_nota or "").strip().lower()


def admite_subnotas(tipo_nota):
    """False para las columnas internas que la planilla no muestra."""
    return clave_de_tipo(tipo_nota) not in _TIPOS_SIN_SUBNOTAS


def normalizar_nota(valor):
    """La nota que se guarda, con dos decimales, o None si no es valida.

    Valida es un numero entre 1 y 5, igual que `NotaPlanillaCreate`. Se
    redondea a dos decimales mitad hacia arriba **antes** de guardarla y de
    promediarla, para que el promedio se calcule sobre lo mismo que queda en
    la base (`numeric(3,2)`).
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)):
        return None
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    numero = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    if numero < 1 or numero > 5:
        return None
    return numero.quantize(_CENTESIMA, rounding=ROUND_HALF_UP)


def promedio_de_notas(notas):
    """Promedio con dos decimales, mitad hacia arriba, o None sin notas.

    Se calcula en centesimas enteras: 4.10 y 4.15 son 410 y 415, el promedio
    exacto es 412.5 y queda en 413, o sea 4.13. Con flotantes, `round()` daria
    4.12 (redondea al par) y (1.00 + 1.01) / 2 saldria 1.00 en vez de 1.01.
    """
    centesimas = [int(normalizar_nota(nota) * 100) for nota in notas]
    if not centesimas:
        return None
    total, cantidad = sum(centesimas), len(centesimas)
    # Mitad hacia arriba con enteros: piso de (total / cantidad + 1/2).
    redondeado = (2 * total + cantidad) // (2 * cantidad)
    return (Decimal(redondeado) / 100).quantize(_CENTESIMA)


def promedio_de_valoraciones(codigos):
    """Carita del promedio de las caritas, o None si no hay ninguna valida.

    Un codigo que no es de la escala no cuenta, igual que en el frontend. El
    promedio es una fraccion exacta: el desempate de 4.5 no depende de como
    redondee un flotante.
    """
    valores = [valor_de_valoracion(codigo) for codigo in codigos if es_valoracion(codigo)]
    if not valores:
        return None
    return valoracion_desde_promedio(Fraction(sum(valores), len(valores)))


def calcular_celda(tipo_evaluacion, calificaciones):
    """`(nota, valoracion)` de la celda a partir de sus calificaciones.

    P2: una subnota vacia no cuenta. Sin ninguna calificacion del tipo de la
    celda devuelve `(None, None)`: la celda queda vacia (P4). En preescolar la
    celda guarda la carita con `nota` vacia, igual que hoy.
    """
    calificaciones = list(calificaciones)
    if tipo_evaluacion == "desarrollo":
        codigos = [valoracion for _, valoracion in calificaciones if valoracion is not None]
        return None, promedio_de_valoraciones(codigos)

    notas = [nota for nota, _ in calificaciones if nota is not None]
    return promedio_de_notas(notas), None


def tipo_de_calificaciones(calificaciones):
    """"desarrollo" si solo hay caritas; "numerica" en cualquier otro caso.

    Lo usa el recalculo al borrar una subnota, que no recibe el tipo de
    evaluacion de la pantalla. En preescolar y primaria da igual: el nivel del
    curso lo fuerza despues con `resolver_tipo_evaluacion`.
    """
    calificaciones = list(calificaciones)
    hay_caritas = any(valoracion is not None for _, valoracion in calificaciones)
    hay_notas = any(nota is not None for nota, _ in calificaciones)
    return "desarrollo" if hay_caritas and not hay_notas else "numerica"


def valor_de_calificacion(nota, valoracion):
    """Lo que viaja en el JSON: la nota como numero o el codigo de la carita."""
    return float(nota) if nota is not None else valoracion


def armar_subnotas_de_planilla(columnas, filas):
    """Las subnotas por tipo y las calificaciones por estudiante.

    `filas` son las de `leer_subnotas_de_planilla`, en orden de creacion:
    `(subnota_id, tipo_nota, nombre, estudiante_id, nota, valoracion)`, con
    `estudiante_id` vacio para una subnota que nadie ha calificado.

    Cada tipo sale con el **nombre exacto de su columna**, para que la pantalla
    los empareje sin normalizar nada. Una subnota cuyo tipo no es una columna
    visible no sale: no hay donde mostrarla.

    Las claves de las calificaciones van como texto, como en Listas de
    seguimiento: JSON solo admite claves de texto.
    """
    columna_por_clave = {}
    for columna in columnas:
        columna_por_clave.setdefault(clave_de_tipo(columna), columna)

    por_tipo = {}
    por_estudiante = {}
    vistas = set()
    for subnota_id, tipo_nota, nombre, estudiante_id, nota, valoracion in filas:
        columna = columna_por_clave.get(clave_de_tipo(tipo_nota))
        if columna is None:
            continue
        if subnota_id not in vistas:
            vistas.add(subnota_id)
            por_tipo.setdefault(columna, []).append({"id": subnota_id, "nombre": nombre})
        if estudiante_id is not None:
            por_estudiante.setdefault(estudiante_id, {})[str(subnota_id)] = (
                valor_de_calificacion(nota, valoracion)
            )

    return por_tipo, por_estudiante
