"""Correccion de mayusculas del texto del observador.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. El frontend aplica lo mismo
al salir del campo, para que la profesora vea el resultado antes de guardar;
esto es la garantia, no la comodidad. Que la logica viva en los dos sitios es
deliberado: cualquier otro camino de escritura queda cubierto.

Reglas, decididas con el usuario:

- mayuscula en la primera letra del texto;
- mayuscula despues de `.`, `?` y `!`;
- **no** despues de `,`, `;` ni `:` -pondria «Se para, Hace desorden»-;
- espacios sobrantes colapsados, y el que falta tras el punto, anadido.

Se guarda el texto **ya corregido**, no el original. Decidido el 2026-09-08: la
profesora ve la correccion antes de guardar y puede rehacerla, asi que lo que
aprueba es lo que queda escrito -y lo que se imprime si el observador acaba ante
una reclamacion-.

**Defecto conocido y aceptado:** con abreviaturas se pasa de listo
(`etc. y luego` -> `etc. Y luego`). Es raro en una observacion, todos los
sistemas que hacen esto lo tienen, y la profesora lo ve en pantalla antes de
guardar. No se complica por eso.
"""
import re

_ESPACIOS = re.compile(r"\s+")

# `[^\W\d_]` es «una letra», con acentos y ñ incluidos. Se usa en vez de
# `[a-zA-Z]` porque el texto es castellano: sin esto, «esto.Ávila» no se
# reconoceria.
_LETRA = r"[^\W\d_]"

# En castellano la frase puede abrir con `¿` o `¡`, y entonces la letra que hay
# que poner en mayuscula NO es el primer caracter. Sin esto, «¿por que?» se
# quedaba en minuscula.
_APERTURA = r"[¿¡\"'«(\[]*"

# Espacio que falta tras el punto. Solo si lo que sigue empieza una frase de
# verdad: asi «mide 1.75 metros» y los puntos suspensivos se quedan como estan.
_FALTA_ESPACIO = re.compile(rf"([.?!])(?={_APERTURA}{_LETRA})", re.UNICODE)

# La letra que abre frase nueva, ya con su espacio delante.
_TRAS_PUNTO = re.compile(rf"([.?!]\s+{_APERTURA})({_LETRA})", re.UNICODE)

# La primera letra del texto, saltando lo que la abra. No usa `texto[0]` porque
# ese puede ser `¿`, una comilla o un parentesis.
_PRIMERA_LETRA = re.compile(rf"^({_APERTURA})({_LETRA})", re.UNICODE)


def normalizar_texto(valor):
    """El texto tal y como debe quedar guardado.

    Devuelve cadena vacia para `None` y para el texto en blanco: los tres campos
    del observador son opcionales por separado, y es el conjunto el que no puede
    estar vacio -eso lo valida el esquema, no esto-.
    """
    texto = _ESPACIOS.sub(" ", str(valor or "").strip())
    if not texto:
        return ""

    texto = _FALTA_ESPACIO.sub(r"\1 ", texto)
    texto = _TRAS_PUNTO.sub(lambda m: m.group(1) + m.group(2).upper(), texto)
    return _PRIMERA_LETRA.sub(
        lambda m: m.group(1) + m.group(2).upper(), texto, count=1
    )
