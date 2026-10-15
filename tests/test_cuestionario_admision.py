"""Entrevista de admisión, paso E10: las preguntas del anexo y sus respuestas.

Ver docs/funcionalidades/ENTREVISTA_ADMISION.md, "Preguntas del anexo (pasos
E8 a E12)". La lista vive solo en el backend: el frontend la pide y arma el
formulario con ella, y el backend revisa cada respuesta contra ella. Estas
pruebas fijan la lista del documento y las reglas de cada tipo de pregunta.
"""
import pytest

from app.core import cuestionario_admision as cuestionario


# La lista del documento, sección por sección y en orden.
CLAVES_POR_SECCION = {
    "datos_personales": ("como_lo_llaman",),
    "familia": (
        "numero_hermanos",
        "lugar_entre_hermanos",
        "quienes_trabajan",
        "situaciones_familia",
        "solucion_conflictos",
    ),
    "vivienda": ("tipo_vivienda", "pasa_tiempo_solo", "con_quien_queda"),
    "nacimiento": (
        "gestacion_normal",
        "parto_normal",
        "nacio_a_termino",
        "dificultad_al_nacer",
    ),
    "alimentacion": ("comidas_del_dia", "alimentos_preferidos", "alimentos_prohibidos"),
    "esfinteres": ("edad_control_esfinteres", "usa_panal"),
    "salud": (
        "dificultad_motora",
        "accidentes_enfermedades",
        "enfermedades_padecidas",
        "lateralidad",
        "miedos",
    ),
    "inclusion": (
        "diagnostico",
        "seguimiento_profesional",
        "profesionales",
        "recomendaciones_profesionales",
        "apoyos_anteriores",
        "situacion_particular",
        "dificultades",
        "informes_profesionales",
        "recomendacion_familia",
    ),
    "lenguaje": (
        "pronunciacion_clara",
        "vocabulario_amplio",
        "corregido_al_hablar",
        "comunica_lo_que_siente",
    ),
    "comportamiento": (
        "rabietas",
        "rompe_juguetes",
        "como_lo_corrigen",
        "pega_sin_causa",
        "a_quien_obedece",
        "pega_a_mayores",
        "irrespeto_lugares_publicos",
        "horas_celular",
        "celular_para_comer",
        "agresivo_sin_celular",
    ),
    "juego_vida_social": (
        "juega_fuera_de_casa",
        "comparte_con_dificultad",
        "mascota",
        "se_relaciona_facilmente",
    ),
    "escolar": (
        "reaccion_situaciones_escolares",
        "acepta_trabajo_integral",
        "ambos_de_acuerdo",
        "capacidad_de_pago",
    ),
    "opinion": ("opinion_edificio",),
}

TIPOS_QUE_NO_SON_SI_NO = {
    "como_lo_llaman": "texto",
    "numero_hermanos": "numero",
    "lugar_entre_hermanos": "numero",
    "quienes_trabajan": "texto",
    "situaciones_familia": "varias",
    "solucion_conflictos": "texto_largo",
    "tipo_vivienda": "una",
    "con_quien_queda": "varias",
    "comidas_del_dia": "varias",
    "alimentos_preferidos": "texto",
    "alimentos_prohibidos": "texto",
    "edad_control_esfinteres": "texto",
    "enfermedades_padecidas": "varias",
    "lateralidad": "una",
    "profesionales": "varias",
    "situacion_particular": "texto_largo",
    "recomendacion_familia": "texto_largo",
    "como_lo_corrigen": "texto_largo",
    "a_quien_obedece": "texto",
    "horas_celular": "numero",
    "reaccion_situaciones_escolares": "texto_largo",
    "ambos_de_acuerdo": "una",
    "opinion_edificio": "una",
}

# Sí / No con un cuadro para escribir: con qué respuesta aparece y qué pide.
DETALLES = {
    "gestacion_normal": ("no", "¿Qué pasó?"),
    "parto_normal": ("no", "¿Qué pasó?"),
    "nacio_a_termino": ("no", "¿Qué pasó?"),
    "dificultad_al_nacer": ("si", "¿Cuál?"),
    "dificultad_motora": ("si", "¿Cuál?"),
    "accidentes_enfermedades": ("si", "¿Cuál?"),
    "miedos": ("si", "¿A qué?"),
    "diagnostico": ("si", "¿Cuál?"),
    "recomendaciones_profesionales": ("si", "¿Cuáles?"),
    "apoyos_anteriores": ("si", "Describa brevemente"),
    "dificultades": ("si", "¿Cuál(es)?"),
    "mascota": ("si", "¿Cuál?"),
}


def _valores(clave):
    return [opcion["valor"] for opcion in cuestionario.PREGUNTAS[clave]["opciones"]]


def _error(datos):
    with pytest.raises(cuestionario.CuestionarioInvalidoError) as exc:
        cuestionario.limpiar_cuestionario(datos)
    return str(exc.value)


# ---------------------------------------------------------------------------
# La lista
# ---------------------------------------------------------------------------


def test_son_las_13_secciones_del_anexo_en_orden():
    assert [s["clave"] for s in cuestionario.SECCIONES] == list(CLAVES_POR_SECCION)
    assert [s["titulo"] for s in cuestionario.SECCIONES] == [
        "Datos personales",
        "Familia",
        "Vivienda",
        "Nacimiento",
        "Alimentación",
        "Control de esfínteres",
        "Salud",
        "Inclusión y necesidades educativas",
        "Lenguaje",
        "Comportamiento",
        "Juego y vida social",
        "Escolar",
        "Opinión de la familia",
    ]


def test_son_las_55_preguntas_del_documento_numeradas_en_orden():
    for seccion in cuestionario.SECCIONES:
        claves = tuple(p["clave"] for p in seccion["preguntas"])
        assert claves == CLAVES_POR_SECCION[seccion["clave"]], seccion["clave"]

    numeros = [p["numero"] for s in cuestionario.SECCIONES for p in s["preguntas"]]
    assert numeros == list(range(1, 56))
    assert len(cuestionario.PREGUNTAS) == 55


def test_cada_pregunta_tiene_el_tipo_del_documento():
    for clave, pregunta in cuestionario.PREGUNTAS.items():
        esperado = TIPOS_QUE_NO_SON_SI_NO.get(clave, "si_no")
        assert pregunta["tipo"] == esperado, clave
        assert pregunta["tipo"] in cuestionario.TIPOS


def test_los_textos_son_los_del_anexo():
    p = cuestionario.PREGUNTAS
    assert p["como_lo_llaman"]["texto"] == "¿Cómo lo llaman en casa?"
    assert p["lugar_entre_hermanos"]["texto"] == (
        "Lugar que ocupa entre los hermanos (1 = el mayor)"
    )
    assert p["irrespeto_lugares_publicos"]["texto"] == (
        "¿Hace rabietas o muestra irrespeto en lugares públicos?"
    )
    assert p["diagnostico"]["texto"] == (
        "¿El estudiante presenta actualmente algún diagnóstico médico, "
        "psicológico, neuropsicológico o condición que debamos conocer para "
        "acompañar adecuadamente su proceso escolar?"
    )
    assert p["opinion_edificio"]["texto"] == (
        "¿Cómo cree usted que es nuestro edificio escolar y sus dependencias?"
    )
    for pregunta in p.values():
        assert pregunta["texto"].strip() == pregunta["texto"]
        assert pregunta["texto"]


def test_no_pregunta_lo_que_puede_discriminar():
    """Decisión 16: ni estado civil de los padres ni religión (T-510 de 1994)."""
    textos = " ".join(
        f"{p['clave']} {p['texto']} "
        + " ".join(o["etiqueta"] for o in p.get("opciones", ()))
        for p in cuestionario.PREGUNTAS.values()
    ).lower()

    for prohibido in ("religi", "estado civil", "estado_civil", "casados", "separados", "credo"):
        assert prohibido not in textos


def test_si_no_ofrece_si_y_no_y_su_detalle_cuando_lo_tiene():
    for clave, pregunta in cuestionario.PREGUNTAS.items():
        if pregunta["tipo"] != "si_no":
            continue
        assert pregunta["opciones"] == [
            {"valor": "si", "etiqueta": "Sí"},
            {"valor": "no", "etiqueta": "No"},
        ]
        if clave in DETALLES:
            con, texto = DETALLES[clave]
            assert pregunta["detalle"] == {"con": con, "texto": texto, "maximo": 250}
        else:
            assert "detalle" not in pregunta, clave


def test_opciones_de_una_y_de_varias():
    assert _valores("situaciones_familia") == [
        "alcoholismo", "drogadiccion", "violencia", "abuso", "ninguno", "otro",
    ]
    assert _valores("tipo_vivienda") == ["casa", "apartamento", "compartida", "otro"]
    assert _valores("con_quien_queda") == ["empleada", "hermanos", "familiares", "otro"]
    assert _valores("comidas_del_dia") == ["desayuno", "almuerzo", "merienda", "cena"]
    assert _valores("enfermedades_padecidas") == [
        "hepatitis", "paperas", "asma", "varicela", "ninguno", "otro",
    ]
    assert _valores("lateralidad") == ["izquierdo", "derecho", "ambidiestro"]
    assert _valores("profesionales") == [
        "psicologia", "neuropsicologia", "fonoaudiologia",
        "terapia_ocupacional", "fisioterapia", "psiquiatria", "otro",
    ]
    assert _valores("ambos_de_acuerdo") == ["si", "no", "no_aplica"]
    assert _valores("opinion_edificio") == ["muy_bueno", "regular", "pesimo"]


def test_las_etiquetas_dicen_ninguna_y_otra_donde_el_anexo_las_dice_asi():
    etiquetas = {
        o["valor"]: o["etiqueta"]
        for o in cuestionario.PREGUNTAS["enfermedades_padecidas"]["opciones"]
    }
    assert etiquetas["ninguno"] == "Ninguna"
    assert etiquetas["otro"] == "Otra"


def test_otro_abre_un_cuadro_solo_donde_el_documento_lo_pone():
    con_otro = {
        clave: pregunta["otro"]["texto"]
        for clave, pregunta in cuestionario.PREGUNTAS.items()
        if "otro" in pregunta
    }

    assert con_otro == {
        "situaciones_familia": "¿Cuál?",
        "tipo_vivienda": "¿Cuál?",
        "con_quien_queda": "¿Quién?",
        "enfermedades_padecidas": "¿Cuál?",
        "profesionales": "¿Cuál?",
    }
    for clave in con_otro:
        assert cuestionario.PREGUNTAS[clave]["otro"]["maximo"] == 250
        assert "otro" in _valores(clave)


def test_ninguno_es_excluyente_en_las_preguntas_5_y_21():
    excluyentes = {
        clave: pregunta["exclusiva"]
        for clave, pregunta in cuestionario.PREGUNTAS.items()
        if "exclusiva" in pregunta
    }

    assert excluyentes == {"situaciones_familia": "ninguno", "enfermedades_padecidas": "ninguno"}


def test_la_26_depende_de_la_25():
    dependientes = {
        clave: pregunta["depende_de"]
        for clave, pregunta in cuestionario.PREGUNTAS.items()
        if "depende_de" in pregunta
    }

    assert dependientes == {
        "profesionales": {"pregunta": "seguimiento_profesional", "respuesta": "si"}
    }


def test_rangos_de_los_numeros_y_limites_de_los_textos():
    p = cuestionario.PREGUNTAS
    assert (p["numero_hermanos"]["minimo"], p["numero_hermanos"]["maximo"]) == (0, 20)
    assert (p["lugar_entre_hermanos"]["minimo"], p["lugar_entre_hermanos"]["maximo"]) == (1, 21)
    assert (p["horas_celular"]["minimo"], p["horas_celular"]["maximo"]) == (0, 24)
    for pregunta in p.values():
        if pregunta["tipo"] == "texto":
            assert pregunta["maximo"] == 150
        if pregunta["tipo"] == "texto_largo":
            assert pregunta["maximo"] == 1000
    assert p["edad_control_esfinteres"]["ayuda"] == "Por ejemplo: 2 años y medio"


def test_el_catalogo_que_sale_es_una_copia():
    """Quien lo reciba (la ruta) no puede cambiar la lista de todos."""
    copia = cuestionario.catalogo()
    copia["secciones"][0]["preguntas"][0]["texto"] = "cambiado"

    assert cuestionario.PREGUNTAS["como_lo_llaman"]["texto"] == "¿Cómo lo llaman en casa?"
    assert cuestionario.catalogo()["secciones"][0]["clave"] == "datos_personales"


# ---------------------------------------------------------------------------
# Revisión de respuestas
# ---------------------------------------------------------------------------


def test_un_bloque_vacio_es_valido():
    assert cuestionario.limpiar_cuestionario({}) == {}


@pytest.mark.parametrize("datos", [[], "hola", 3, True])
def test_el_bloque_tiene_que_ser_un_objeto(datos):
    assert "bloque" in _error(datos)


def test_una_pregunta_que_no_existe_no_se_guarda():
    mensaje = _error({"religion": "x"})

    assert '"religion"' in mensaje
    assert "no existe" in mensaje


def test_una_respuesta_nula_es_sin_responder():
    assert cuestionario.limpiar_cuestionario({"usa_panal": None, "como_lo_llaman": None}) == {}


def test_el_resultado_sale_en_el_orden_de_la_lista():
    limpio = cuestionario.limpiar_cuestionario(
        {
            "opinion_edificio": {"opcion": "regular"},
            "como_lo_llaman": "Juancho",
            "usa_panal": {"respuesta": "no"},
        }
    )

    assert list(limpio) == ["como_lo_llaman", "usa_panal", "opinion_edificio"]


# Sí / No ------------------------------------------------------------------


def test_si_no_guarda_la_respuesta():
    assert cuestionario.limpiar_cuestionario({"usa_panal": {"respuesta": "si"}}) == {
        "usa_panal": {"respuesta": "si"}
    }


@pytest.mark.parametrize("respuesta", ["Sí", "SI", "talvez", 1, True])
def test_si_no_solo_admite_si_o_no(respuesta):
    mensaje = _error({"usa_panal": {"respuesta": respuesta}})

    assert "Pregunta 18" in mensaje


def test_el_detalle_se_guarda_recortado_con_la_respuesta_que_lo_pide():
    limpio = cuestionario.limpiar_cuestionario(
        {
            "dificultad_motora": {"respuesta": "si", "detalle": "  Usa plantillas "},
            "parto_normal": {"respuesta": "no", "detalle": "Cesárea"},
        }
    )

    assert limpio == {
        "dificultad_motora": {"respuesta": "si", "detalle": "Usa plantillas"},
        "parto_normal": {"respuesta": "no", "detalle": "Cesárea"},
    }


def test_un_detalle_en_blanco_no_se_guarda():
    limpio = cuestionario.limpiar_cuestionario(
        {"dificultad_motora": {"respuesta": "si", "detalle": "   "}}
    )

    assert limpio == {"dificultad_motora": {"respuesta": "si"}}


def test_no_hay_detalle_con_la_otra_respuesta():
    mensaje = _error({"dificultad_motora": {"respuesta": "no", "detalle": "x"}})

    assert "Pregunta 19" in mensaje


def test_no_hay_detalle_en_una_pregunta_que_no_lo_tiene():
    assert "Pregunta 18" in _error({"usa_panal": {"respuesta": "no", "detalle": "x"}})


def test_el_detalle_cabe_en_250():
    largo = {"dificultad_motora": {"respuesta": "si", "detalle": "x" * 250}}
    assert cuestionario.limpiar_cuestionario(largo)["dificultad_motora"]["detalle"] == "x" * 250

    assert "Pregunta 19" in _error(
        {"dificultad_motora": {"respuesta": "si", "detalle": "x" * 251}}
    )


def test_si_no_sin_respuesta_es_sin_responder_pero_no_con_detalle():
    assert cuestionario.limpiar_cuestionario({"usa_panal": {}}) == {}
    assert "Pregunta 19" in _error({"dificultad_motora": {"detalle": "x"}})


@pytest.mark.parametrize(
    "valor", ["si", ["si"], {"respuesta": "si", "extra": 1}, {"opcion": "si"}]
)
def test_si_no_con_otra_forma_no_vale(valor):
    assert "Pregunta 18" in _error({"usa_panal": valor})


# Una opción ---------------------------------------------------------------


def test_una_opcion_guarda_la_opcion():
    assert cuestionario.limpiar_cuestionario({"lateralidad": {"opcion": "derecho"}}) == {
        "lateralidad": {"opcion": "derecho"}
    }


def test_una_opcion_que_no_existe_no_vale():
    assert "Pregunta 22" in _error({"lateralidad": {"opcion": "zurdo"}})


def test_otro_guarda_su_texto_solo_si_se_eligio_otro():
    limpio = cuestionario.limpiar_cuestionario(
        {"tipo_vivienda": {"opcion": "otro", "otro": " Finca "}}
    )
    assert limpio == {"tipo_vivienda": {"opcion": "otro", "otro": "Finca"}}

    assert "Pregunta 7" in _error({"tipo_vivienda": {"opcion": "casa", "otro": "Finca"}})


def test_otro_sin_texto_es_solo_otro():
    limpio = cuestionario.limpiar_cuestionario({"tipo_vivienda": {"opcion": "otro", "otro": ""}})

    assert limpio == {"tipo_vivienda": {"opcion": "otro"}}


def test_no_hay_otro_en_una_pregunta_que_no_lo_tiene():
    assert "Pregunta 22" in _error({"lateralidad": {"opcion": "derecho", "otro": "x"}})


def test_no_aplica_en_la_53():
    assert cuestionario.limpiar_cuestionario({"ambos_de_acuerdo": {"opcion": "no_aplica"}}) == {
        "ambos_de_acuerdo": {"opcion": "no_aplica"}
    }


# Varias -------------------------------------------------------------------


def test_varias_guarda_las_marcadas_en_el_orden_de_la_lista():
    limpio = cuestionario.limpiar_cuestionario(
        {"comidas_del_dia": {"marcadas": ["cena", "desayuno"]}}
    )

    assert limpio == {"comidas_del_dia": {"marcadas": ["desayuno", "cena"]}}


@pytest.mark.parametrize("valor", [{"marcadas": []}, {"marcadas": None}, {}])
def test_varias_sin_marcar_es_sin_responder(valor):
    assert cuestionario.limpiar_cuestionario({"comidas_del_dia": valor}) == {}


@pytest.mark.parametrize("marcadas", [["brunch"], ["cena", "cena"], "cena", [1]])
def test_varias_con_opciones_que_no_valen(marcadas):
    assert "Pregunta 14" in _error({"comidas_del_dia": {"marcadas": marcadas}})


def test_ninguno_no_se_combina_con_otras():
    mensaje = _error({"situaciones_familia": {"marcadas": ["ninguno", "violencia"]}})

    assert "Pregunta 5" in mensaje
    assert cuestionario.limpiar_cuestionario(
        {"situaciones_familia": {"marcadas": ["ninguno"]}}
    ) == {"situaciones_familia": {"marcadas": ["ninguno"]}}


def test_otro_en_varias_solo_si_se_marco_otro():
    limpio = cuestionario.limpiar_cuestionario(
        {"con_quien_queda": {"marcadas": ["otro", "hermanos"], "otro": "La vecina"}}
    )
    assert limpio == {
        "con_quien_queda": {"marcadas": ["hermanos", "otro"], "otro": "La vecina"}
    }

    assert "Pregunta 9" in _error(
        {"con_quien_queda": {"marcadas": ["hermanos"], "otro": "La vecina"}}
    )
    assert "Pregunta 14" in _error({"comidas_del_dia": {"marcadas": ["cena"], "otro": "x"}})


# Número -------------------------------------------------------------------


@pytest.mark.parametrize("valor", [0, 3, 20])
def test_numero_dentro_del_rango(valor):
    assert cuestionario.limpiar_cuestionario({"numero_hermanos": valor}) == {
        "numero_hermanos": valor
    }


@pytest.mark.parametrize("valor", [-1, 21, 2.5, 3.0, "3", True, [3]])
def test_numero_fuera_del_rango_o_que_no_es_entero(valor):
    assert "Pregunta 2" in _error({"numero_hermanos": valor})


def test_el_lugar_entre_hermanos_empieza_en_1():
    assert "Pregunta 3" in _error({"lugar_entre_hermanos": 0})


# Texto --------------------------------------------------------------------


def test_texto_recortado_y_en_blanco_sin_responder():
    limpio = cuestionario.limpiar_cuestionario(
        {"como_lo_llaman": "  Juancho ", "quienes_trabajan": "   "}
    )

    assert limpio == {"como_lo_llaman": "Juancho"}


def test_limites_de_texto_corto_y_largo():
    assert cuestionario.limpiar_cuestionario({"como_lo_llaman": "x" * 150})
    assert "Pregunta 1" in _error({"como_lo_llaman": "x" * 151})
    assert cuestionario.limpiar_cuestionario({"solucion_conflictos": "x" * 1000})
    assert "Pregunta 6" in _error({"solucion_conflictos": "x" * 1001})


@pytest.mark.parametrize("valor", [3, ["x"], {"texto": "x"}])
def test_texto_que_no_es_texto(valor):
    assert "Pregunta 1" in _error({"como_lo_llaman": valor})


# Dependencias -------------------------------------------------------------


def test_la_26_solo_se_responde_si_la_25_es_si():
    con_si = {
        "seguimiento_profesional": {"respuesta": "si"},
        "profesionales": {"marcadas": ["psicologia"]},
    }
    assert cuestionario.limpiar_cuestionario(con_si) == con_si

    sin_25 = {"profesionales": {"marcadas": ["psicologia"]}}
    con_no = {
        "seguimiento_profesional": {"respuesta": "no"},
        "profesionales": {"marcadas": ["psicologia"]},
    }
    assert "Pregunta 26" in _error(sin_25)
    assert "Pregunta 26" in _error(con_no)


def test_una_entrevista_completa_y_realista_pasa():
    datos = {
        "como_lo_llaman": "Juancho",
        "numero_hermanos": 2,
        "lugar_entre_hermanos": 1,
        "situaciones_familia": {"marcadas": ["ninguno"]},
        "tipo_vivienda": {"opcion": "apartamento"},
        "pasa_tiempo_solo": {"respuesta": "no"},
        "con_quien_queda": {"marcadas": ["familiares"]},
        "parto_normal": {"respuesta": "no", "detalle": "Cesárea programada"},
        "comidas_del_dia": {"marcadas": ["desayuno", "almuerzo", "cena"]},
        "edad_control_esfinteres": "2 años y medio",
        "usa_panal": {"respuesta": "no"},
        "enfermedades_padecidas": {"marcadas": ["varicela"]},
        "lateralidad": {"opcion": "derecho"},
        "diagnostico": {"respuesta": "no"},
        "seguimiento_profesional": {"respuesta": "si"},
        "profesionales": {"marcadas": ["fonoaudiologia"]},
        "horas_celular": 1,
        "irrespeto_lugares_publicos": {"respuesta": "no"},
        "mascota": {"respuesta": "si", "detalle": "Un perro"},
        "ambos_de_acuerdo": {"opcion": "si"},
        "opinion_edificio": {"opcion": "muy_bueno"},
    }

    assert cuestionario.limpiar_cuestionario(datos) == datos
