"""Entrevista de admisión, paso E2: lo que entra por HTTP.

Ver docs/funcionalidades/ENTREVISTA_ADMISION.md. Como en listas de
seguimiento, el esquema repite las reglas que la base ya impone, para que
salgan como un 422 con mensaje y no como un 500 desde PostgreSQL.
"""
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.repositories import admisiones_repository as repositorio
from app.schemas import admision as esquemas


MIGRACION = Path(__file__).resolve().parents[1] / "migrations" / "20261013_admisiones.sql"


def _aspirante(**cambios):
    datos = {
        "nombre": "Lina",
        "apellido": "Díaz",
        "autoriza_datos": True,
        "autoriza_nombre": "Marta Díaz",
    }
    datos.update(cambios)
    return datos


def _tamanos_de_la_migracion():
    """Columna -> tamaño de su VARCHAR, o None si es TEXT, leído del SQL."""
    texto = MIGRACION.read_text(encoding="utf-8")
    tamanos = {}
    for nombre, tipo, tamano in re.findall(
        r"^\s+([a-z_]+) (VARCHAR\((\d+)\)|TEXT)", texto, flags=re.MULTILINE
    ):
        tamanos[nombre] = int(tamano) if tamano else None
    return tamanos


def test_registrar_pide_solo_los_datos_del_aspirante():
    assert tuple(esquemas.AdmisionCreate.model_fields) == repositorio.COLUMNAS_ASPIRANTE


def test_editar_pide_los_datos_del_aspirante_y_de_la_entrevista():
    assert tuple(esquemas.AdmisionUpdate.model_fields) == (
        repositorio.COLUMNAS_ASPIRANTE + repositorio.COLUMNAS_ENTREVISTA
    )


def test_ningun_cuerpo_cambia_el_resultado_ni_el_enlace_al_estudiante():
    datos = esquemas.AdmisionUpdate(
        **_aspirante(),
        resultado="aprobado",
        motivo_resultado="x",
        estudiante_id=5,
        anio_lectivo_id=9,
    ).model_dump()

    for campo in ("resultado", "motivo_resultado", "estudiante_id", "anio_lectivo_id"):
        assert campo not in datos


def test_lo_minimo_es_nombre_apellido_y_la_autorizacion():
    datos = esquemas.AdmisionCreate(**_aspirante()).model_dump()

    assert datos["nombre"] == "Lina"
    assert datos["autoriza_datos"] is True
    assert datos["documento_identidad"] is None
    assert datos["curso_id"] is None


@pytest.mark.parametrize("campo", ["nombre", "apellido", "autoriza_datos", "autoriza_nombre"])
def test_falta_un_dato_obligatorio(campo):
    datos = _aspirante()
    del datos[campo]

    with pytest.raises(ValidationError):
        esquemas.AdmisionCreate(**datos)


@pytest.mark.parametrize("campo", ["nombre", "apellido", "autoriza_nombre"])
def test_un_obligatorio_en_blanco_no_vale(campo):
    with pytest.raises(ValidationError):
        esquemas.AdmisionCreate(**_aspirante(**{campo: "   "}))


def test_sin_autorizacion_de_datos_no_se_registra():
    with pytest.raises(ValidationError) as exc:
        esquemas.AdmisionCreate(**_aspirante(autoriza_datos=False))

    assert esquemas.MENSAJE_AUTORIZACION_OBLIGATORIA in str(exc.value)


def test_tampoco_se_puede_quitar_la_autorizacion_al_editar():
    with pytest.raises(ValidationError):
        esquemas.AdmisionUpdate(**_aspirante(autoriza_datos=False))


def test_recorta_espacios_y_guarda_lo_vacio_como_nulo():
    datos = esquemas.AdmisionUpdate(
        **_aspirante(
            nombre="  Lina ",
            documento_identidad="   ",
            acudiente_telefono=" 300 ",
            observaciones="",
        )
    ).model_dump()

    assert datos["nombre"] == "Lina"
    # Un documento vacío contaría como repetido en el índice único por año.
    assert datos["documento_identidad"] is None
    assert datos["acudiente_telefono"] == "300"
    assert datos["observaciones"] is None


def test_el_curso_si_viene_es_un_id_positivo():
    with pytest.raises(ValidationError):
        esquemas.AdmisionCreate(**_aspirante(curso_id=0))

    assert esquemas.AdmisionCreate(**_aspirante(curso_id=7)).curso_id == 7


def test_las_fechas_se_leen_como_fechas():
    datos = esquemas.AdmisionUpdate(
        **_aspirante(fecha_nacimiento="2019-03-04", fecha_entrevista="2026-10-20")
    )

    assert datos.fecha_nacimiento.isoformat() == "2019-03-04"
    assert datos.fecha_entrevista.isoformat() == "2026-10-20"


def test_cada_texto_cabe_en_su_columna_y_uno_mas_largo_da_422():
    tamanos = _tamanos_de_la_migracion()
    campos = repositorio.COLUMNAS_ASPIRANTE + repositorio.COLUMNAS_ENTREVISTA
    textos = [c for c in campos if c in tamanos]

    # 8 del aspirante y 13 de la entrevista.
    assert len(textos) == 21
    for campo in textos:
        tamano = tamanos[campo]
        if tamano is None:
            # TEXT: no tiene límite en la base.
            esquemas.AdmisionUpdate(**_aspirante(**{campo: "x" * 5000}))
            continue
        esquemas.AdmisionUpdate(**_aspirante(**{campo: "x" * tamano}))
        with pytest.raises(ValidationError):
            esquemas.AdmisionUpdate(**_aspirante(**{campo: "x" * (tamano + 1)}))


def test_el_filtro_de_resultado_solo_admite_los_tres_resultados():
    assert set(esquemas.RESULTADOS_ADMISION) == {"pendiente", "aprobado", "no_aprobado"}
