"""Preguntas del anexo de la entrevista de admisión y la revisión de sus respuestas.

Ver `docs/funcionalidades/ENTREVISTA_ADMISION.md`, "Preguntas del anexo
(pasos E8 a E12)". Las respuestas se guardan juntas en
`admisiones.cuestionario` (un bloque JSON), cada una bajo la clave de su
pregunta; una pregunta sin responder no aparece.

**La lista vive solo aquí.** El frontend la pide (`GET
/admisiones/cuestionario`) y arma el formulario con ella, y el backend revisa
cada respuesta contra ella: así no hay dos copias que se puedan desordenar.

Reglas de la lista, decididas con el usuario:

- La clave de una pregunta **nunca se reutiliza ni cambia de significado**:
  las respuestas guardadas la usan.
- No se pregunta estado civil de los padres ni religión, aunque estén en el
  anexo en papel (decisión 16, no discriminación, T-510 de 1994).
- Ninguna pregunta es obligatoria: el papel tampoco obliga.

Qué se guarda, por tipo:

- `si_no`: `{"respuesta": "si" | "no", "detalle": "..."}`; el detalle solo
  con la respuesta que lo pide.
- `una`: `{"opcion": "...", "otro": "..."}`; "otro" solo si se eligió "Otro".
- `varias`: `{"marcadas": [...], "otro": "..."}`; "Ninguno" no se combina.
- `numero`: un entero dentro de su rango.
- `texto` y `texto_largo`: el texto recortado.

Un texto en blanco, una lista vacía o `null` cuentan como sin responder y
no se guardan.
"""
from copy import deepcopy


TIPOS = ("si_no", "una", "varias", "numero", "texto", "texto_largo")

LIMITE_TEXTO = 150
LIMITE_TEXTO_LARGO = 1000
LIMITE_DETALLE = 250  # el cuadro del detalle y el de "Otro"


def _opcion(valor, etiqueta):
    return {"valor": valor, "etiqueta": etiqueta}


def _si_no(clave, texto, detalle_con=None, detalle=None):
    opciones = [_opcion("si", "Sí"), _opcion("no", "No")]
    pregunta = {"clave": clave, "texto": texto, "tipo": "si_no", "opciones": opciones}
    if detalle is not None:
        pregunta["detalle"] = {"con": detalle_con, "texto": detalle, "maximo": LIMITE_DETALLE}
    return pregunta


def _con_opciones(tipo, clave, texto, opciones, otro=None, exclusiva=None):
    pregunta = {
        "clave": clave,
        "texto": texto,
        "tipo": tipo,
        "opciones": [_opcion(valor, etiqueta) for valor, etiqueta in opciones],
    }
    if otro is not None:
        pregunta["otro"] = {"texto": otro, "maximo": LIMITE_DETALLE}
    if exclusiva is not None:
        pregunta["exclusiva"] = exclusiva
    return pregunta


def _una(clave, texto, opciones, otro=None):
    return _con_opciones("una", clave, texto, opciones, otro=otro)


def _varias(clave, texto, opciones, otro=None, exclusiva=None):
    return _con_opciones("varias", clave, texto, opciones, otro=otro, exclusiva=exclusiva)


def _numero(clave, texto, minimo, maximo):
    return {"clave": clave, "texto": texto, "tipo": "numero", "minimo": minimo, "maximo": maximo}


def _texto(clave, texto, ayuda=None):
    pregunta = {"clave": clave, "texto": texto, "tipo": "texto", "maximo": LIMITE_TEXTO}
    if ayuda is not None:
        pregunta["ayuda"] = ayuda
    return pregunta


def _texto_largo(clave, texto):
    return {"clave": clave, "texto": texto, "tipo": "texto_largo", "maximo": LIMITE_TEXTO_LARGO}


def _seccion(clave, titulo, *preguntas):
    return {"clave": clave, "titulo": titulo, "preguntas": list(preguntas)}


_SECCIONES_SIN_NUMERO = (
    _seccion(
        "datos_personales",
        "Datos personales",
        _texto("como_lo_llaman", "¿Cómo lo llaman en casa?"),
    ),
    _seccion(
        "familia",
        "Familia",
        _numero("numero_hermanos", "Número de hermanos", 0, 20),
        _numero("lugar_entre_hermanos", "Lugar que ocupa entre los hermanos (1 = el mayor)", 1, 21),
        _texto("quienes_trabajan", "¿En casa quiénes trabajan?"),
        _varias(
            "situaciones_familia",
            "En la familia, ¿hay algún caso de…?",
            (
                ("alcoholismo", "Alcoholismo"),
                ("drogadiccion", "Drogadicción"),
                ("violencia", "Violencia"),
                ("abuso", "Abuso"),
                ("ninguno", "Ninguno"),
                ("otro", "Otro"),
            ),
            otro="¿Cuál?",
            exclusiva="ninguno",
        ),
        _texto_largo("solucion_conflictos", "¿Cómo solucionan sus conflictos familiares?"),
    ),
    _seccion(
        "vivienda",
        "Vivienda",
        _una(
            "tipo_vivienda",
            "Tipo de vivienda",
            (
                ("casa", "Casa"),
                ("apartamento", "Apartamento"),
                ("compartida", "Compartida"),
                ("otro", "Otro"),
            ),
            otro="¿Cuál?",
        ),
        _si_no("pasa_tiempo_solo", "¿Pasa el niño(a) algún tiempo solo?"),
        _varias(
            "con_quien_queda",
            "¿Con quién queda el niño(a) cuando los padres trabajan?",
            (
                ("empleada", "Empleada"),
                ("hermanos", "Hermanos"),
                ("familiares", "Familiares"),
                ("otro", "Otro"),
            ),
            otro="¿Quién?",
        ),
    ),
    _seccion(
        "nacimiento",
        "Nacimiento",
        _si_no("gestacion_normal", "¿El proceso de gestación fue normal?", "no", "¿Qué pasó?"),
        _si_no("parto_normal", "¿El parto fue normal?", "no", "¿Qué pasó?"),
        _si_no("nacio_a_termino", "¿Nació a término completo?", "no", "¿Qué pasó?"),
        _si_no("dificultad_al_nacer", "¿Tuvo alguna dificultad al nacer?", "si", "¿Cuál?"),
    ),
    _seccion(
        "alimentacion",
        "Alimentación",
        _varias(
            "comidas_del_dia",
            "¿Cuáles de las cuatro comidas del día hace?",
            (
                ("desayuno", "Desayuno"),
                ("almuerzo", "Almuerzo"),
                ("merienda", "Merienda"),
                ("cena", "Cena"),
            ),
        ),
        _texto("alimentos_preferidos", "Alimentos preferidos"),
        _texto("alimentos_prohibidos", "Alimentos prohibidos por el médico"),
    ),
    _seccion(
        "esfinteres",
        "Control de esfínteres",
        _texto(
            "edad_control_esfinteres",
            "¿A qué edad controló esfínteres?",
            ayuda="Por ejemplo: 2 años y medio",
        ),
        _si_no("usa_panal", "¿Usa pañal desechable?"),
    ),
    _seccion(
        "salud",
        "Salud",
        _si_no("dificultad_motora", "¿Tiene alguna dificultad motora?", "si", "¿Cuál?"),
        _si_no(
            "accidentes_enfermedades",
            "¿Sufrió algún accidente, convulsiones o enfermedades?",
            "si",
            "¿Cuál?",
        ),
        _varias(
            "enfermedades_padecidas",
            "Enfermedades que padeció",
            (
                ("hepatitis", "Hepatitis"),
                ("paperas", "Paperas"),
                ("asma", "Asma"),
                ("varicela", "Varicela"),
                ("ninguno", "Ninguna"),
                ("otro", "Otra"),
            ),
            otro="¿Cuál?",
            exclusiva="ninguno",
        ),
        _una(
            "lateralidad",
            "¿Qué lado predomina más?",
            (
                ("izquierdo", "Izquierdo"),
                ("derecho", "Derecho"),
                ("ambidiestro", "Ambidiestro"),
            ),
        ),
        _si_no("miedos", "¿Le tiene miedo a algo?", "si", "¿A qué?"),
    ),
    _seccion(
        "inclusion",
        "Inclusión y necesidades educativas",
        _si_no(
            "diagnostico",
            "¿El estudiante presenta actualmente algún diagnóstico médico, "
            "psicológico, neuropsicológico o condición que debamos conocer para "
            "acompañar adecuadamente su proceso escolar?",
            "si",
            "¿Cuál?",
        ),
        _si_no(
            "seguimiento_profesional",
            "¿El estudiante ha recibido o recibe actualmente algún tipo de "
            "seguimiento o acompañamiento profesional?",
        ),
        {
            **_varias(
                "profesionales",
                "En caso afirmativo, indique cuál",
                (
                    ("psicologia", "Psicología"),
                    ("neuropsicologia", "Neuropsicología"),
                    ("fonoaudiologia", "Fonoaudiología"),
                    ("terapia_ocupacional", "Terapia ocupacional"),
                    ("fisioterapia", "Fisioterapia"),
                    ("psiquiatria", "Psiquiatría"),
                    ("otro", "Otro"),
                ),
                otro="¿Cuál?",
            ),
            "depende_de": {"pregunta": "seguimiento_profesional", "respuesta": "si"},
        },
        _si_no(
            "recomendaciones_profesionales",
            "¿Actualmente cuenta con recomendaciones o indicaciones de "
            "profesionales para favorecer su desempeño y bienestar en el entorno "
            "escolar?",
            "si",
            "¿Cuáles?",
        ),
        _si_no(
            "apoyos_anteriores",
            "¿El estudiante ha contado anteriormente con algún tipo de apoyo o "
            "ajuste en el ámbito escolar?",
            "si",
            "Describa brevemente",
        ),
        _texto_largo(
            "situacion_particular",
            "¿Existe alguna situación, comportamiento, dificultad o necesidad "
            "particular que consideren importante que el colegio conozca para "
            "brindar un adecuado acompañamiento al estudiante?",
        ),
        _si_no(
            "dificultades",
            "¿El estudiante presenta alguna dificultad relacionada con el "
            "aprendizaje, comunicación, lenguaje, atención, comportamiento, "
            "interacción social, autonomía o manejo de emociones?",
            "si",
            "¿Cuál(es)?",
        ),
        _si_no(
            "informes_profesionales",
            "¿Cuenta actualmente con informes, valoraciones o recomendaciones de "
            "profesionales que puedan ser compartidos con la institución para "
            "orientar su proceso de acompañamiento?",
        ),
        _texto_largo(
            "recomendacion_familia",
            "¿Hay alguna recomendación especial que la familia considere "
            "importante para favorecer la adaptación, participación y aprendizaje "
            "del estudiante en el colegio?",
        ),
    ),
    _seccion(
        "lenguaje",
        "Lenguaje",
        _si_no("pronunciacion_clara", "¿Su pronunciación es clara?"),
        _si_no("vocabulario_amplio", "¿Su vocabulario es amplio?"),
        _si_no("corregido_al_hablar", "Cuando se equivoca al hablar, ¿es corregido?"),
        _si_no("comunica_lo_que_siente", "¿Comunica lo que siente?"),
    ),
    _seccion(
        "comportamiento",
        "Comportamiento",
        _si_no("rabietas", "¿Manifiesta rabietas?"),
        _si_no("rompe_juguetes", "¿Rompe juguetes?"),
        _texto_largo(
            "como_lo_corrigen",
            "¿Cómo lo corrigen cuando presenta ese tipo de comportamiento?",
        ),
        _si_no("pega_sin_causa", "¿Pega sin causa?"),
        _texto("a_quien_obedece", "¿A quién obedece más?"),
        _si_no("pega_a_mayores", "¿Le pega a los padres o mayores?"),
        # Decisión 15: en el anexo esta pregunta sale cortada.
        _si_no(
            "irrespeto_lugares_publicos",
            "¿Hace rabietas o muestra irrespeto en lugares públicos?",
        ),
        _numero("horas_celular", "¿Cuántas horas diarias usa el celular?", 0, 24),
        _si_no("celular_para_comer", "¿Usa el celular para comer?"),
        _si_no(
            "agresivo_sin_celular",
            "¿Muestra actitudes agresivas cuando le quitan el celular?",
        ),
    ),
    _seccion(
        "juego_vida_social",
        "Juego y vida social",
        _si_no("juega_fuera_de_casa", "¿Juega fuera de casa?"),
        _si_no("comparte_con_dificultad", "¿Comparte con dificultad sus juguetes?"),
        _si_no("mascota", "¿Tiene alguna mascota?", "si", "¿Cuál?"),
        _si_no("se_relaciona_facilmente", "¿Se relaciona fácilmente con los demás?"),
    ),
    _seccion(
        "escolar",
        "Escolar",
        _texto_largo(
            "reaccion_situaciones_escolares",
            "¿Cómo reaccionaría frente a situaciones escolares de su hijo(a)? "
            "(golpes, mordidas, etc.)",
        ),
        _si_no(
            "acepta_trabajo_integral",
            "¿Está dispuesto a dejar que la escuela y las docentes realicen un "
            "trabajo integral en su hijo(a)?",
        ),
        # "No aplica": una familia de un solo padre o madre no puede decir "ambos".
        _una(
            "ambos_de_acuerdo",
            "¿Estuvieron ambos de acuerdo para colocar a su hijo(a) en esta escuela?",
            (("si", "Sí"), ("no", "No"), ("no_aplica", "No aplica")),
        ),
        _si_no(
            "capacidad_de_pago",
            "¿Están en capacidad de sufragar los gastos de una escuela privada?",
        ),
    ),
    _seccion(
        "opinion",
        "Opinión de la familia",
        _una(
            "opinion_edificio",
            "¿Cómo cree usted que es nuestro edificio escolar y sus dependencias?",
            (("muy_bueno", "Muy bueno"), ("regular", "Regular"), ("pesimo", "Pésimo")),
        ),
    ),
)


def _numerar(secciones):
    numero = 0
    numeradas = []
    for seccion in secciones:
        preguntas = []
        for pregunta in seccion["preguntas"]:
            numero += 1
            preguntas.append({"numero": numero, **pregunta})
        numeradas.append({**seccion, "preguntas": preguntas})
    return tuple(numeradas)


SECCIONES = _numerar(_SECCIONES_SIN_NUMERO)

PREGUNTAS = {
    pregunta["clave"]: pregunta for seccion in SECCIONES for pregunta in seccion["preguntas"]
}


def catalogo():
    """La lista para el frontend. Es una copia: nadie cambia la de todos."""
    return {"secciones": deepcopy(list(SECCIONES))}


# ---------------------------------------------------------------------------
# Revisión de respuestas
# ---------------------------------------------------------------------------


class CuestionarioInvalidoError(ValueError):
    """Una respuesta no corresponde a su pregunta. El mensaje se muestra tal cual."""


def _invalida(pregunta, problema):
    texto = pregunta["texto"]
    if len(texto) > 60:
        texto = texto[:57].rstrip() + "…"
    return CuestionarioInvalidoError(f"Pregunta {pregunta['numero']} («{texto}»): {problema}")


def _exigir_objeto(pregunta, valor, claves_permitidas):
    if not isinstance(valor, dict) or not set(valor) <= claves_permitidas:
        raise _invalida(pregunta, "la respuesta no tiene la forma esperada.")


def _texto_opcional(pregunta, valor, maximo, nombre):
    """Un texto recortado, o `None` si no llegó o quedó en blanco."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise _invalida(pregunta, f"{nombre} tiene que ser un texto.")
    valor = valor.strip()
    if not valor:
        return None
    if len(valor) > maximo:
        raise _invalida(pregunta, f"{nombre} no puede pasar de {maximo} caracteres.")
    return valor


def _valores(pregunta):
    return [opcion["valor"] for opcion in pregunta["opciones"]]


def _limpiar_si_no(pregunta, valor):
    _exigir_objeto(pregunta, valor, {"respuesta", "detalle"})
    respuesta = valor.get("respuesta")
    detalle = _texto_opcional(pregunta, valor.get("detalle"), LIMITE_DETALLE, "el detalle")
    if respuesta is None:
        if detalle is not None:
            raise _invalida(pregunta, "falta elegir Sí o No.")
        return None
    if respuesta not in ("si", "no"):
        raise _invalida(pregunta, "la respuesta tiene que ser Sí o No.")
    limpia = {"respuesta": respuesta}
    if detalle is not None:
        configuracion = pregunta.get("detalle")
        if configuracion is None or respuesta != configuracion["con"]:
            raise _invalida(pregunta, "con esa respuesta no se escribe un detalle.")
        limpia["detalle"] = detalle
    return limpia


def _otro(pregunta, valor, elegido):
    otro = _texto_opcional(pregunta, valor.get("otro"), LIMITE_DETALLE, "lo escrito en «Otro»")
    if otro is not None and ("otro" not in pregunta or not elegido):
        raise _invalida(pregunta, "solo se escribe algo en «Otro» si se elige «Otro».")
    return otro


def _limpiar_una(pregunta, valor):
    _exigir_objeto(pregunta, valor, {"opcion", "otro"})
    opcion = valor.get("opcion")
    if opcion is not None and opcion not in _valores(pregunta):
        raise _invalida(pregunta, "esa opción no existe.")
    otro = _otro(pregunta, valor, elegido=opcion == "otro")
    if opcion is None:
        return None
    limpia = {"opcion": opcion}
    if otro is not None:
        limpia["otro"] = otro
    return limpia


def _limpiar_varias(pregunta, valor):
    _exigir_objeto(pregunta, valor, {"marcadas", "otro"})
    marcadas = valor.get("marcadas") or []
    validas = _valores(pregunta)
    if not isinstance(marcadas, list) or any(m not in validas for m in marcadas):
        raise _invalida(pregunta, "alguna de las opciones marcadas no existe.")
    if len(set(marcadas)) != len(marcadas):
        raise _invalida(pregunta, "una opción está marcada dos veces.")
    exclusiva = pregunta.get("exclusiva")
    if exclusiva in marcadas and len(marcadas) > 1:
        etiqueta = next(o["etiqueta"] for o in pregunta["opciones"] if o["valor"] == exclusiva)
        raise _invalida(pregunta, f"«{etiqueta}» no se marca junto con otras opciones.")
    otro = _otro(pregunta, valor, elegido="otro" in marcadas)
    if not marcadas:
        return None
    limpia = {"marcadas": [v for v in validas if v in marcadas]}
    if otro is not None:
        limpia["otro"] = otro
    return limpia


def _limpiar_numero(pregunta, valor):
    # `True` también es un `int` en Python: no vale como número.
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise _invalida(pregunta, "tiene que ser un número entero.")
    if not pregunta["minimo"] <= valor <= pregunta["maximo"]:
        raise _invalida(
            pregunta, f"tiene que estar entre {pregunta['minimo']} y {pregunta['maximo']}."
        )
    return valor


def _limpiar_texto(pregunta, valor):
    return _texto_opcional(pregunta, valor, pregunta["maximo"], "la respuesta")


_LIMPIEZA_POR_TIPO = {
    "si_no": _limpiar_si_no,
    "una": _limpiar_una,
    "varias": _limpiar_varias,
    "numero": _limpiar_numero,
    "texto": _limpiar_texto,
    "texto_largo": _limpiar_texto,
}


def limpiar_cuestionario(datos):
    """Revisa el bloque de respuestas y lo devuelve limpio, en el orden de la lista.

    Lanza `CuestionarioInvalidoError` con un mensaje listo para mostrar si
    algo no corresponde a su pregunta.
    """
    if not isinstance(datos, dict):
        raise CuestionarioInvalidoError(
            "Las respuestas de la entrevista tienen que llegar como un bloque."
        )
    respuestas = {}
    for clave, valor in datos.items():
        pregunta = PREGUNTAS.get(clave)
        if pregunta is None:
            raise CuestionarioInvalidoError(f'La pregunta "{clave}" no existe en la entrevista.')
        if valor is None:
            continue
        limpia = _LIMPIEZA_POR_TIPO[pregunta["tipo"]](pregunta, valor)
        if limpia is not None:
            respuestas[clave] = limpia

    for clave in respuestas:
        depende_de = PREGUNTAS[clave].get("depende_de")
        if depende_de is None:
            continue
        anterior = respuestas.get(depende_de["pregunta"]) or {}
        if anterior.get("respuesta") != depende_de["respuesta"]:
            numero = PREGUNTAS[depende_de["pregunta"]]["numero"]
            raise _invalida(
                PREGUNTAS[clave], f"solo se responde si la pregunta {numero} es «Sí»."
            )

    return {clave: respuestas[clave] for clave in PREGUNTAS if clave in respuestas}
