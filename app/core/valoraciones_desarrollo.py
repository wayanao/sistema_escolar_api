"""Escala de valoracion del desarrollo infantil (las caritas de preescolar).

**Es una copia exacta** de `frontend-react/src/constants/valoracionesDesarrollo.js`
y de las reglas de `frontend-react/src/utils/valoracionesDesarrollo.js`. Hasta
las subnotas de la planilla el backend no la necesitaba: guardaba la carita
tal como llegaba. Ahora calcula la carita de una celda a partir de sus
subnotas (ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, P8), y tiene que
llegar a la misma que muestra la pantalla.

Si la escala cambia, cambia en los dos repos. Cada uno tiene una prueba que
fija los cuatro codigos y sus valores, para que una copia no se aparte de la
otra sin que nadie lo note.

Sin base de datos, sin HTTP.
"""

# En orden descendente por valor, igual que en el frontend: el desempate de
# `valoracion_desde_promedio` depende de este orden.
VALORACIONES_DESARROLLO = (
    ("destacado", 5),
    ("logrado", 4),
    ("proceso", 3),
    ("apoyo", 2),
)

_VALOR_POR_CODIGO = dict(VALORACIONES_DESARROLLO)


def es_valoracion(codigo):
    """True si el codigo es una de las caritas de la escala."""
    return codigo in _VALOR_POR_CODIGO


def valor_de_valoracion(codigo):
    """Equivalencia numerica de una carita, o None si no es de la escala."""
    return _VALOR_POR_CODIGO.get(codigo)


def valoracion_desde_promedio(promedio):
    """Carita cuyo valor esta mas cerca del promedio, o None sin promedio.

    Ante un empate gana la mas alta, porque la escala se recorre de mayor a
    menor y solo se cambia de opcion si la nueva esta **estrictamente** mas
    cerca. Asi 4.5 es "destacado" y 4.33 es "logrado", igual que en el
    frontend.
    """
    if promedio is None:
        return None

    codigo_cercano, valor_cercano = VALORACIONES_DESARROLLO[0]
    for codigo, valor in VALORACIONES_DESARROLLO[1:]:
        if abs(valor - promedio) < abs(valor_cercano - promedio):
            codigo_cercano, valor_cercano = codigo, valor
    return codigo_cercano
