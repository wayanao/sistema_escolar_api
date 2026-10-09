"""Fase 6.3b: el boletín de un año cerrado usa la foto de materias ocultas.

Decisión 13: un año cerrado se ve como el día en que se cerró. Sus boletines
ocultan las materias de `anios_lectivos_materias_ocultas`, aunque después se
activen o desactiven. El año activo y el de preparación siguen ocultando las
materias inactivas, como hoy, y sin año el texto de la consulta no cambia.
"""
import pytest

from app.repositories import boletin_repository

FILTRO_DE_HOY = "COALESCE(LOWER(m.estado), 'activo') = 'activo'"


class CursorQueAnota:
    def __init__(self):
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchall(self):
        return []


def test_sin_anio_el_filtro_es_exactamente_el_de_hoy():
    assert boletin_repository._materia_visible(None) == (FILTRO_DE_HOY, ())


def test_con_anio_un_anio_cerrado_o_reabierto_usa_su_foto():
    sql, params = boletin_repository._materia_visible(3)

    sql = " ".join(sql.split())
    assert params == (3, 3)
    assert sql == (
        "CASE WHEN (SELECT estado FROM anios_lectivos WHERE id = %s) "
        "IN ('cerrado', 'reabierto') "
        "THEN NOT EXISTS ( SELECT 1 FROM anios_lectivos_materias_ocultas o "
        "WHERE o.anio_lectivo_id = %s AND o.materia_id = m.id ) "
        f"ELSE {FILTRO_DE_HOY} END"
    )


# (argumentos, parámetros de hoy sin año)
CONSULTAS = {
    "leer_materias_del_estudiante": ((8, 2, "ASISTENCIA"), (2, 2, 8, "ASISTENCIA")),
    "leer_planilla_vigente": ((8, 2, "ASISTENCIA"), (2, 8, "ASISTENCIA")),
}


@pytest.mark.parametrize("nombre", sorted(CONSULTAS))
def test_sin_anio_las_dos_consultas_quedan_como_hoy(nombre):
    argumentos, params = CONSULTAS[nombre]
    cursor = CursorQueAnota()

    getattr(boletin_repository, nombre)(cursor, *argumentos)

    [(sql, recibidos)] = cursor.consultas
    assert f"AND {FILTRO_DE_HOY} ORDER BY" in sql
    assert "anios_lectivos_materias_ocultas" not in sql
    assert recibidos == params


@pytest.mark.parametrize("nombre", sorted(CONSULTAS))
def test_con_anio_las_dos_consultas_miran_la_foto_del_anio(nombre):
    argumentos, params = CONSULTAS[nombre]
    cursor = CursorQueAnota()

    getattr(boletin_repository, nombre)(cursor, *argumentos, anio_lectivo_id=3)

    [(sql, recibidos)] = cursor.consultas
    filtro, params_filtro = boletin_repository._materia_visible(3)
    assert f"AND {' '.join(filtro.split())} ORDER BY" in sql
    # El año del curso va primero; el del filtro, al final, tras el nombre
    # de la materia excluida.
    assert recibidos == (3, *params, *params_filtro)
