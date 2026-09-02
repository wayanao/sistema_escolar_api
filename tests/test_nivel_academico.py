"""Reglas puras de nivel academico. Sin base de datos, sin React, sin DOM."""
from app.core.nivel_academico import (
    NOMBRE_MATERIA_ASISTENCIA_JORNADA,
    es_asignacion_de_jornada,
    resolver_tipo_evaluacion,
    tipo_evaluacion_forzado,
)


def test_preescolar_fuerza_desarrollo():
    assert tipo_evaluacion_forzado("preescolar") == "desarrollo"


def test_primaria_no_fuerza_nada():
    assert tipo_evaluacion_forzado("primaria") is None


def test_nivel_desconocido_o_ausente_no_fuerza_nada():
    assert tipo_evaluacion_forzado(None) is None
    assert tipo_evaluacion_forzado("bachillerato") is None
    assert tipo_evaluacion_forzado("") is None


def test_preescolar_ignora_lo_que_pida_el_cliente():
    assert resolver_tipo_evaluacion("preescolar", "numerica") == "desarrollo"
    assert resolver_tipo_evaluacion("preescolar", None) == "desarrollo"


def test_primaria_respeta_lo_solicitado():
    assert resolver_tipo_evaluacion("primaria", "desarrollo") == "desarrollo"
    assert resolver_tipo_evaluacion("primaria", "numerica") == "numerica"


def test_primaria_sin_solicitud_cae_a_numerica():
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
