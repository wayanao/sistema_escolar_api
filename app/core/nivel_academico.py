"""Reglas de negocio por nivel academico de un curso (preescolar/primaria).

Centraliza que exige cada nivel para no repetir el condicional en cada
controlador. Ver docs/funcionalidades/NIVEL_ACADEMICO.md.

Un curso sin `nivel` definido no fuerza nada: es exactamente el
comportamiento anterior a esta funcionalidad. Un curso con nivel definido
-preescolar o primaria- siempre tiene su tipo de evaluacion fijo; ninguno
de los dos es libre.
"""

REGLAS_POR_NIVEL = {
    "preescolar": {
        "tipo_evaluacion_forzado": "desarrollo",
        "asistencia_por_jornada": True,
    },
    "primaria": {
        "tipo_evaluacion_forzado": "numerica",
        "asistencia_por_jornada": False,
    },
}


def tipo_evaluacion_forzado(nivel):
    """Tipo de evaluacion que un nivel exige, o None si el nivel no esta
    definido (unico caso libre)."""
    reglas = REGLAS_POR_NIVEL.get(nivel)
    return reglas["tipo_evaluacion_forzado"] if reglas else None


def resolver_tipo_evaluacion(nivel, tipo_evaluacion_solicitado):
    """Tipo de evaluacion que de verdad se guarda, segun el nivel del curso.

    Un nivel definido siempre fuerza su tipo -preescolar "desarrollo",
    primaria "numerica"-, sin importar lo que pida el cliente. Solo un curso
    sin nivel definido es libre, con "numerica" como respaldo cuando no
    llega nada: es el comportamiento anterior a esta funcionalidad,
    preservado para no afectar a los cursos que todavia no se han
    clasificado.
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


def asistencia_por_jornada_requerida(nivel):
    """True si el nivel exige que la asistencia se tome por una asignacion
    reservada de jornada completa, en vez de por cada materia."""
    reglas = REGLAS_POR_NIVEL.get(nivel)
    return bool(reglas and reglas["asistencia_por_jornada"])


MENSAJE_ASISTENCIA_REQUIERE_JORNADA = (
    'Este curso es de preescolar. Usa la asignación "Asistencia diaria" '
    "para registrar asistencia."
)


def asistencia_rechazada_por_nivel(nivel, nombre_materia):
    """True si, segun el nivel del curso, esta asignacion NO es valida para
    registrar asistencia -por ejemplo, una materia real (Matematicas,
    Lenguaje...) en un curso preescolar, que exige la asignacion reservada
    de jornada en su lugar.

    Un curso sin nivel definido o de primaria nunca rechaza nada: es
    exactamente el comportamiento anterior a esta funcionalidad.
    """
    if not asistencia_por_jornada_requerida(nivel):
        return False
    return not es_asignacion_de_jornada(nombre_materia)
