"""Reglas de negocio por nivel academico de un curso (preescolar/primaria).

Centraliza que exige cada nivel para no repetir el condicional en cada
controlador. Ver docs/funcionalidades/NIVEL_ACADEMICO.md.

Un nivel ausente o desconocido (curso sin `nivel` definido) no fuerza nada:
es exactamente el comportamiento anterior a esta funcionalidad.
"""

REGLAS_POR_NIVEL = {
    "preescolar": {
        "tipo_evaluacion_forzado": "desarrollo",
        "asistencia_por_jornada": True,
    },
    "primaria": {
        "tipo_evaluacion_forzado": None,
        "asistencia_por_jornada": False,
    },
}


def tipo_evaluacion_forzado(nivel):
    """Tipo de evaluacion que un nivel exige, o None si el nivel es libre."""
    reglas = REGLAS_POR_NIVEL.get(nivel)
    return reglas["tipo_evaluacion_forzado"] if reglas else None


def resolver_tipo_evaluacion(nivel, tipo_evaluacion_solicitado):
    """Tipo de evaluacion que de verdad se guarda, segun el nivel del curso.

    Si el nivel fuerza un tipo (hoy, preescolar -> "desarrollo"), ese gana
    siempre, sin importar lo que pida el cliente. Si el nivel es libre o no
    esta definido, se conserva lo solicitado, con "numerica" como respaldo
    cuando no llega nada.
    """
    forzado = tipo_evaluacion_forzado(nivel)
    if forzado:
        return forzado
    return tipo_evaluacion_solicitado or "numerica"
