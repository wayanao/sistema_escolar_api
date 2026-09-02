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


# ---------------------------------------------------------------------------
# Asistencia por jornada (preescolar)
# ---------------------------------------------------------------------------

NOMBRE_MATERIA_ASISTENCIA_JORNADA = "ASISTENCIA DIARIA"
"""Nombre reservado de la materia usada para tomar asistencia por jornada
completa en un curso de preescolar, en vez de una vez por cada materia real.

No es una tabla ni una columna nueva: es una convencion sobre el modelo de
asignaciones que ya existe. El administrador crea, para cada curso de
preescolar, una asignacion con este nombre de materia y la maestra titular
como profesora, con un horario que cubra el bloque institucional completo
(Mañana 06:30-12:30 o Tarde 12:30-18:30, segun la jornada del curso) -
exactamente igual que cualquier otra asignacion, desde la pantalla de
Asignaciones ya existente. Esa asignacion se usa despues como cualquier otra
para POST /asistencia, su historial y "mis clases"; no requiere ningun
endpoint ni tabla nuevos.

El backend normaliza todo nombre de materia a mayusculas, espacio simple y
sin espacios en los extremos al crearla (ver
app/controllers/materia_controller.py), asi que este valor ya esta en esa
forma canonica: una comparacion exacta contra el nombre que devuelve la API
es confiable sin duplicar esa normalizacion aqui.
"""


def es_asignacion_de_jornada(nombre_materia):
    """True si el nombre de materia es el reservado para asistencia por
    jornada completa (ver NOMBRE_MATERIA_ASISTENCIA_JORNADA)."""
    return (nombre_materia or "").strip().upper() == NOMBRE_MATERIA_ASISTENCIA_JORNADA
