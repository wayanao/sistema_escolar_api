"""Reglas puras de nivel academico. Sin base de datos, sin React, sin DOM."""
from app.core.nivel_academico import resolver_tipo_evaluacion, tipo_evaluacion_forzado


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
