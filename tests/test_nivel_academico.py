"""Reglas puras de nivel academico. Sin base de datos, sin React, sin DOM."""
from app.core.nivel_academico import (
    MENSAJE_ASISTENCIA_REQUIERE_JORNADA,
    NOMBRE_MATERIA_ASISTENCIA_JORNADA,
    asistencia_por_jornada_requerida,
    asistencia_rechazada_por_nivel,
    es_asignacion_de_jornada,
    resolver_tipo_evaluacion,
    tipo_evaluacion_forzado,
)


def test_preescolar_fuerza_desarrollo():
    assert tipo_evaluacion_forzado("preescolar") == "desarrollo"


def test_primaria_fuerza_numerica():
    assert tipo_evaluacion_forzado("primaria") == "numerica"


def test_nivel_desconocido_o_ausente_no_fuerza_nada():
    assert tipo_evaluacion_forzado(None) is None
    assert tipo_evaluacion_forzado("bachillerato") is None
    assert tipo_evaluacion_forzado("") is None


def test_preescolar_ignora_lo_que_pida_el_cliente():
    assert resolver_tipo_evaluacion("preescolar", "numerica") == "desarrollo"
    assert resolver_tipo_evaluacion("preescolar", None) == "desarrollo"


def test_primaria_ignora_lo_que_pida_el_cliente():
    assert resolver_tipo_evaluacion("primaria", "desarrollo") == "numerica"
    assert resolver_tipo_evaluacion("primaria", "numerica") == "numerica"
    assert resolver_tipo_evaluacion("primaria", None) == "numerica"


def test_curso_sin_nivel_definido_mantiene_el_comportamiento_anterior():
    assert resolver_tipo_evaluacion(None, "desarrollo") == "desarrollo"
    assert resolver_tipo_evaluacion(None, None) == "numerica"


def test_el_nombre_reservado_ya_esta_en_forma_canonica():
    """El backend normaliza materias a mayusculas/espacio simple al crearlas;
    la constante debe coincidir con esa forma para que la comparacion exacta
    sea confiable."""
    assert NOMBRE_MATERIA_ASISTENCIA_JORNADA == "ASISTENCIA DIARIA"


def test_reconoce_el_nombre_reservado_exacto():
    assert es_asignacion_de_jornada("ASISTENCIA DIARIA") is True


def test_es_tolerante_a_mayusculas_y_espacios_sueltos():
    assert es_asignacion_de_jornada("  asistencia diaria  ") is True


def test_no_reconoce_una_materia_distinta():
    assert es_asignacion_de_jornada("Matemáticas") is False
    assert es_asignacion_de_jornada(None) is False
    assert es_asignacion_de_jornada("") is False


def test_solo_preescolar_exige_asistencia_por_jornada():
    assert asistencia_por_jornada_requerida("preescolar") is True
    assert asistencia_por_jornada_requerida("primaria") is False
    assert asistencia_por_jornada_requerida(None) is False
    assert asistencia_por_jornada_requerida("bachillerato") is False


def test_rechaza_una_materia_normal_en_preescolar():
    assert asistencia_rechazada_por_nivel("preescolar", "Matemáticas") is True
    assert asistencia_rechazada_por_nivel("preescolar", "Lenguaje") is True


def test_acepta_la_asignacion_de_jornada_en_preescolar():
    assert asistencia_rechazada_por_nivel("preescolar", "Asistencia diaria") is False
    assert asistencia_rechazada_por_nivel("preescolar", "ASISTENCIA DIARIA") is False


def test_primaria_y_sin_nivel_nunca_rechazan_nada():
    assert asistencia_rechazada_por_nivel("primaria", "Matemáticas") is False
    assert asistencia_rechazada_por_nivel(None, "Matemáticas") is False


def test_el_mensaje_de_rechazo_nombra_la_asignacion_reservada():
    assert "Asistencia diaria" in MENSAJE_ASISTENCIA_REQUIERE_JORNADA
    assert "preescolar" in MENSAJE_ASISTENCIA_REQUIERE_JORNADA
