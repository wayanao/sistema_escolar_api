"""Fase 5.5: matricular estudiantes en el año en preparación.

Las pruebas usan dobles de base de datos. No crean 2027, no escriben en un
tenant real y no ejecutan migraciones.
"""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from psycopg2 import IntegrityError

from app.controllers import anios_lectivos_controller as controlador
from app.repositories import anios_lectivos_repository as repositorio
from app.routes import anios_lectivos as rutas
from app.schemas import anio_lectivo as esquemas
from app.schemas.estudiante import EstudianteCreate


class CursorFalso:
    def __init__(self, una=(), todas=()):
        self.una = list(una)
        self.todas = list(todas)
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.una.pop(0) if self.una else None

    def fetchall(self):
        return self.todas.pop(0) if self.todas else []


def _promocion(**cambios):
    clase = getattr(esquemas, "PromocionEstudiantes")
    datos = {
        "curso_origen_id": 10,
        "curso_destino_id": 20,
        "estudiante_ids": [1, 2],
    }
    datos.update(cambios)
    return clase(**datos)


def _estudiante_nuevo(**cambios):
    datos = {
        "nombre": "Lina",
        "apellido": "Díaz",
        "documento_identidad": "1001",
        "curso_id": 20,
    }
    datos.update(cambios)
    return EstudianteCreate(**datos)


@pytest.fixture
def entorno_matriculas(monkeypatch):
    estado = SimpleNamespace(
        activo=(2, 2026, "activo"),
        destino=(3, 2027, "preparacion"),
        curso_origen={
            "id": 10,
            "nombre": "PRIMERO A",
            "jornada": "Mañana",
            "anio_lectivo_id": 2,
            "anio": 2026,
            "estado_anio": "activo",
        },
        curso_destino={
            "id": 20,
            "nombre": "SEGUNDO A",
            "jornada": "Mañana",
            "anio_lectivo_id": 3,
            "anio": 2027,
            "estado_anio": "preparacion",
        },
        candidatos=[
            {
                "id": 1,
                "nombre": "Ana",
                "apellido": "Pérez",
                "documento_identidad": "101",
                "estado": "activo",
                "curso_destino_id": None,
            },
            {
                "id": 2,
                "nombre": "Beto",
                "apellido": "Ruiz",
                "documento_identidad": "102",
                "estado": "activo",
                "curso_destino_id": None,
            },
            {
                "id": 3,
                "nombre": "Cora",
                "apellido": "Gil",
                "documento_identidad": "103",
                "estado": "retirado",
                "curso_destino_id": 20,
            },
        ],
        valores={
            1: [
                {
                    "id": 71,
                    "tipo_pago_origen_id": 30,
                    "tipo_pago_origen_nombre": "MENSUALIDAD",
                    "tipo_pago_destino_id": 40,
                    "tipo_pago_destino_nombre": "MENSUALIDAD",
                    "valor": 180000,
                    "motivo": "Beca parcial",
                    "activo": True,
                }
            ],
            2: [],
            55: [],
        },
        eventos=[],
        commits=0,
        rollbacks=0,
        fallar_matricula_id=None,
    )
    cursor = object()

    @contextmanager
    def get_cursor_falso(commit=False):
        estado.eventos.append(("abre", commit))
        try:
            yield cursor
        except Exception:
            estado.rollbacks += 1
            raise
        else:
            if commit:
                estado.commits += 1
        finally:
            estado.eventos.append(("cierra",))

    def leer_activo(cursor_recibido):
        estado.eventos.append(("activo", cursor_recibido is cursor))
        return estado.activo

    def leer_destino(cursor_recibido, anio_id):
        estado.eventos.append(("destino", cursor_recibido is cursor, anio_id))
        return estado.destino

    def leer_curso(cursor_recibido, curso_id):
        estado.eventos.append(("curso", curso_id))
        if curso_id == 10:
            return estado.curso_origen
        if curso_id == 20:
            return estado.curso_destino
        return None

    def listar_candidatos(cursor_recibido, curso_id, origen_id, destino_id):
        estado.eventos.append(
            ("candidatos", cursor_recibido is cursor, curso_id, origen_id, destino_id)
        )
        return estado.candidatos

    def insertar_matricula(cursor_recibido, estudiante_id, curso_id, anio_id):
        estado.eventos.append(
            ("matricula", cursor_recibido is cursor, estudiante_id, curso_id, anio_id)
        )
        if estudiante_id == estado.fallar_matricula_id:
            raise IntegrityError("matrícula duplicada")
        return 1000 + estudiante_id

    def listar_valores(cursor_recibido, estudiante_id, origen_id, destino_id):
        estado.eventos.append(
            ("valores", cursor_recibido is cursor, estudiante_id, origen_id, destino_id)
        )
        return estado.valores.get(estudiante_id, [])

    def insertar_valor(cursor_recibido, estudiante_id, valor):
        estado.eventos.append(
            (
                "valor",
                cursor_recibido is cursor,
                estudiante_id,
                valor["tipo_pago_destino_id"],
            )
        )
        return 2000 + valor["id"]

    def insertar_estudiante(cursor_recibido, valores):
        estado.eventos.append(
            ("estudiante", cursor_recibido is cursor, valores)
        )
        return 55

    def sincronizar(cursor_recibido, estudiante_id):
        estado.eventos.append(
            ("sincroniza", cursor_recibido is cursor, estudiante_id)
        )

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    dobles = {
        "leer_anio_activo_para_actualizar": leer_activo,
        "leer_anio_lectivo_para_actualizar": leer_destino,
        "leer_curso_para_matricula": leer_curso,
        "listar_candidatos_matricula": listar_candidatos,
        "insertar_matricula_en_anio": insertar_matricula,
        "listar_valores_especiales_para_copiar": listar_valores,
        "insertar_valor_especial_copiado": insertar_valor,
        "sincronizar_curso_vigente": sincronizar,
    }
    for nombre, doble in dobles.items():
        monkeypatch.setattr(
            controlador.anios_lectivos_repository, nombre, doble, raising=False
        )
    monkeypatch.setattr(
        controlador.estudiantes_repository,
        "insertar_estudiante",
        insertar_estudiante,
        raising=False,
    )
    return estado


def test_el_cuerpo_de_promocion_rechaza_ids_repetidos_y_vacios():
    clase = getattr(esquemas, "PromocionEstudiantes")

    with pytest.raises(ValueError):
        clase(curso_origen_id=10, curso_destino_id=20, estudiante_ids=[])
    with pytest.raises(ValueError):
        clase(curso_origen_id=10, curso_destino_id=20, estudiante_ids=[1, 1])


def test_consultar_candidatos_usa_el_curso_activo_y_muestra_si_ya_se_matriculo(
    entorno_matriculas,
):
    funcion = getattr(controlador, "listar_candidatos_matricula_controller")

    respuesta = funcion(3, 10)

    assert respuesta["anio_origen"] == {"id": 2, "anio": 2026}
    assert respuesta["anio_destino"] == {"id": 3, "anio": 2027}
    assert respuesta["curso_origen"] == {
        "id": 10,
        "nombre": "PRIMERO A",
        "jornada": "Mañana",
    }
    assert [c["id"] for c in respuesta["candidatos"]] == [1, 2, 3]
    assert respuesta["candidatos"][0]["matriculado_en_destino"] is False
    assert respuesta["candidatos"][2]["matriculado_en_destino"] is True
    assert ("candidatos", True, 10, 2, 3) in entorno_matriculas.eventos


def test_promueve_solo_los_marcados_y_copia_sus_valores_especiales(
    entorno_matriculas,
):
    funcion = getattr(controlador, "promover_estudiantes_controller")

    respuesta = funcion(3, _promocion(estudiante_ids=[1, 2]))

    matriculas = [e for e in entorno_matriculas.eventos if e[0] == "matricula"]
    assert matriculas == [
        ("matricula", True, 1, 20, 3),
        ("matricula", True, 2, 20, 3),
    ]
    assert not any(e[0] == "matricula" and e[2] == 3 for e in entorno_matriculas.eventos)
    assert respuesta["matriculados"] == [1, 2]
    assert respuesta["cantidad_matriculados"] == 2
    assert respuesta["valores_especiales_copiados"] == [
        {
            "id": 2071,
            "estudiante_id": 1,
            "tipo_pago_origen_id": 30,
            "tipo_pago_id": 40,
            "tipo_pago_nombre": "MENSUALIDAD",
            "valor": 180000.0,
            "motivo": "Beca parcial",
            "activo": True,
            "estado": "revisar",
        }
    ]
    assert entorno_matriculas.commits == 1
    assert entorno_matriculas.rollbacks == 0


@pytest.mark.parametrize("ids", [[99], [3]])
def test_rechaza_quien_no_pertenece_al_curso_o_ya_esta_matriculado(
    entorno_matriculas, ids
):
    funcion = getattr(controlador, "promover_estudiantes_controller")
    error = getattr(controlador, "CandidatosMatriculaInvalidosError")

    with pytest.raises(error):
        funcion(3, _promocion(estudiante_ids=ids))

    assert not any(e[0] == "matricula" for e in entorno_matriculas.eventos)
    assert entorno_matriculas.rollbacks == 1


def test_rechaza_promover_a_quien_tiene_marca_de_salida(entorno_matriculas):
    """Fase 6.2b: la marca y la matrícula siguiente se excluyen."""
    entorno_matriculas.candidatos[1]["estado_salida"] = "egresado"

    with pytest.raises(
        controlador.CandidatosMatriculaInvalidosError,
        match="Los estudiantes 2 están marcados como que no siguen",
    ):
        controlador.promover_estudiantes_controller(
            3, _promocion(estudiante_ids=[1, 2])
        )

    assert not any(e[0] == "matricula" for e in entorno_matriculas.eventos)
    assert entorno_matriculas.rollbacks == 1


def test_los_candidatos_dicen_su_marca_de_salida(entorno_matriculas):
    """Fase 6.5: el usuario decidió marcar la salida en la pantalla de
    promoción (2026-10-09), así que la lista dice quién ya está marcado. Es
    un campo agregado: los demás no cambian."""
    entorno_matriculas.candidatos[0]["estado_salida"] = "retirado"

    respuesta = controlador.listar_candidatos_matricula_controller(3, 10)

    assert set(respuesta["candidatos"][0]) == {
        "id",
        "nombre",
        "apellido",
        "documento_identidad",
        "estado",
        "matriculado_en_destino",
        "curso_destino_id",
        "estado_salida",
    }
    assert [c["estado_salida"] for c in respuesta["candidatos"]] == [
        "retirado",
        None,
        None,
    ]


def test_rechaza_un_curso_origen_que_no_es_del_anio_activo(entorno_matriculas):
    entorno_matriculas.curso_origen["anio_lectivo_id"] = 9
    funcion = getattr(controlador, "listar_candidatos_matricula_controller")
    error = getattr(controlador, "CursoMatriculaInvalidoError")

    with pytest.raises(error, match="año activo"):
        funcion(3, 10)


def test_rechaza_un_curso_destino_que_no_es_del_anio_en_preparacion(
    entorno_matriculas,
):
    entorno_matriculas.curso_destino["anio_lectivo_id"] = 9
    funcion = getattr(controlador, "promover_estudiantes_controller")
    error = getattr(controlador, "CursoMatriculaInvalidoError")

    with pytest.raises(error, match="año en preparación"):
        funcion(3, _promocion())

    assert entorno_matriculas.rollbacks == 1


def test_un_valor_sin_concepto_equivalente_revierte_toda_la_promocion(
    entorno_matriculas,
):
    entorno_matriculas.valores[1][0]["tipo_pago_destino_id"] = None
    funcion = getattr(controlador, "promover_estudiantes_controller")
    error = getattr(controlador, "ValoresEspecialesInconsistentesError")

    with pytest.raises(error, match="MENSUALIDAD"):
        funcion(3, _promocion(estudiante_ids=[1]))

    assert entorno_matriculas.commits == 0
    assert entorno_matriculas.rollbacks == 1


def test_un_choque_concurrente_de_matricula_se_informa_y_revierte(
    entorno_matriculas,
):
    entorno_matriculas.fallar_matricula_id = 2
    funcion = getattr(controlador, "promover_estudiantes_controller")
    error = getattr(controlador, "CandidatosMatriculaInvalidosError")

    with pytest.raises(error, match="ya tiene matrícula"):
        funcion(3, _promocion(estudiante_ids=[1, 2]))

    assert entorno_matriculas.commits == 0
    assert entorno_matriculas.rollbacks == 1


# Hasta el paso E7 de la entrevista de admisión, esta prueba fijaba que el
# alta directa creaba los datos globales y solo la matrícula de preparación.
# Esa parte vive en `_crear_estudiante_en_preparacion` y la sigue usando la
# matrícula desde una admisión: se fija aquí, llamándola dentro de una
# transacción como lo hace `matricular_aspirante_en_preparacion`.
def test_crear_en_preparacion_crea_solo_la_matricula_y_deja_curso_vigente_nulo(
    entorno_matriculas,
):
    with controlador.get_cursor(commit=True) as cursor:
        estudiante_id, matricula_id = controlador._crear_estudiante_en_preparacion(
            cursor, entorno_matriculas.destino, _estudiante_nuevo()
        )

    nombres = [evento[0] for evento in entorno_matriculas.eventos]
    assert nombres.index("estudiante") < nombres.index("matricula")
    assert nombres.index("matricula") < nombres.index("sincroniza")
    assert ("matricula", True, 55, 20, 3) in entorno_matriculas.eventos
    assert ("sincroniza", True, 55) in entorno_matriculas.eventos
    valores_globales = next(e[2] for e in entorno_matriculas.eventos if e[0] == "estudiante")
    assert len(valores_globales) == 34
    assert 20 not in valores_globales
    assert (estudiante_id, matricula_id) == (55, 1055)
    assert entorno_matriculas.commits == 1


# Paso E7: un estudiante nuevo del año en preparación solo entra desde una
# admisión aprobada (decisión 3 de docs/funcionalidades/ENTREVISTA_ADMISION.md).
def test_el_alta_directa_en_preparacion_queda_cerrada(entorno_matriculas):
    error = getattr(controlador, "AltaDirectaCerradaError")

    with pytest.raises(error) as exc:
        controlador.crear_estudiante_en_preparacion_controller(3, _estudiante_nuevo())

    assert str(exc.value) == (
        "Un estudiante nuevo en 2027 se matricula desde su entrevista aprobada "
        "(Admisiones)."
    )
    nombres = [evento[0] for evento in entorno_matriculas.eventos]
    for escritura in ("estudiante", "matricula", "sincroniza"):
        assert escritura not in nombres
    assert entorno_matriculas.commits == 0
    assert entorno_matriculas.eventos[-1] == ("cierra",)


def test_en_un_anio_que_no_esta_en_preparacion_dice_lo_de_siempre(entorno_matriculas):
    entorno_matriculas.destino = (3, 2027, "activo")

    with pytest.raises(controlador.AnioLectivoDestinoInvalidoError) as exc:
        controlador.crear_estudiante_en_preparacion_controller(3, _estudiante_nuevo())

    assert str(exc.value) == "Solo se puede matricular en un año en preparación."


def test_la_ruta_del_alta_directa_responde_409_con_el_mensaje(monkeypatch):
    mensaje = (
        "Un estudiante nuevo en 2027 se matricula desde su entrevista aprobada "
        "(Admisiones)."
    )

    def cerrada(*_args, **_kwargs):
        raise controlador.AltaDirectaCerradaError(mensaje)

    monkeypatch.setattr(rutas, "crear_estudiante_en_preparacion_controller", cerrada)

    with pytest.raises(HTTPException) as exc:
        rutas.crear_estudiante_en_preparacion(3, _estudiante_nuevo())

    assert exc.value.status_code == 409
    assert exc.value.detail == mensaje


def test_las_tres_rutas_nuevas_exigen_admin():
    from app.dependencies import get_current_active_admin

    paths = {
        "/anios-lectivos/{anio_lectivo_id}/matriculas/candidatos",
        "/anios-lectivos/{anio_lectivo_id}/matriculas/promocion",
        "/anios-lectivos/{anio_lectivo_id}/estudiantes",
    }
    encontradas = {ruta.path: ruta for ruta in rutas.router.routes if ruta.path in paths}

    assert set(encontradas) == paths
    for ruta in encontradas.values():
        assert get_current_active_admin in [
            dependencia.call for dependencia in ruta.dependant.dependencies
        ]


def test_las_rutas_traducen_errores_de_matricula_a_409(monkeypatch):
    error = getattr(controlador, "CursoMatriculaInvalidoError")

    def rechazar(*_args, **_kwargs):
        raise error("Curso incorrecto")

    monkeypatch.setattr(rutas, "listar_candidatos_matricula_controller", rechazar)
    monkeypatch.setattr(rutas, "promover_estudiantes_controller", rechazar)
    monkeypatch.setattr(rutas, "crear_estudiante_en_preparacion_controller", rechazar)

    llamadas = [
        lambda: rutas.listar_candidatos_matricula(3, 10),
        lambda: rutas.promover_estudiantes(3, _promocion()),
        lambda: rutas.crear_estudiante_en_preparacion(3, _estudiante_nuevo()),
    ]
    for llamada in llamadas:
        with pytest.raises(HTTPException) as exc:
            llamada()
        assert exc.value.status_code == 409
        assert exc.value.detail == "Curso incorrecto"


# ---------------------------------------------------------------------------
# SQL: las matrículas mandan y los valores se enlazan por su concepto origen.
# ---------------------------------------------------------------------------


def test_los_candidatos_salen_de_la_matricula_del_curso_no_del_curso_legacy():
    cursor = CursorFalso(
        todas=[[(1, "Ana", "Pérez", "101", "activo", None)]]
    )

    filas = getattr(repositorio, "listar_candidatos_matricula")(cursor, 10, 2, 3)

    sql, params = cursor.consultas[0]
    assert "FROM matriculas origen" in sql
    assert "origen.curso_id = %s" in sql
    assert "LEFT JOIN matriculas destino" in sql
    assert "e.curso_id" not in sql
    assert params == (3, 2, 10)
    assert filas[0]["curso_destino_id"] is None


def test_los_candidatos_traen_la_marca_de_salida_de_su_matricula_activa():
    cursor = CursorFalso(
        todas=[[(1, "Ana", "Pérez", "101", "activo", None, "retirado")]]
    )

    filas = repositorio.listar_candidatos_matricula(cursor, 10, 2, 3)

    sql, _params = cursor.consultas[0]
    assert "origen.estado_salida" in sql
    assert filas[0]["estado_salida"] == "retirado"


def test_insertar_matricula_no_modifica_el_curso_vigente():
    cursor = CursorFalso(una=[(81,)])

    matricula_id = getattr(repositorio, "insertar_matricula_en_anio")(
        cursor, 1, 20, 3
    )

    sql, params = cursor.consultas[0]
    assert matricula_id == 81
    assert "INSERT INTO matriculas" in sql
    assert "estudiantes" not in sql
    assert "UPDATE" not in sql
    assert params == (1, 20, 3)


def test_los_valores_especiales_se_mapean_por_tipo_pago_origen():
    cursor = CursorFalso(
        todas=[
            [
                (
                    71,
                    30,
                    "MENSUALIDAD",
                    40,
                    "MENSUALIDAD",
                    180000,
                    "Beca parcial",
                    True,
                )
            ]
        ]
    )

    filas = getattr(repositorio, "listar_valores_especiales_para_copiar")(
        cursor, 1, 2, 3
    )

    sql, params = cursor.consultas[0]
    assert "destino.tipo_pago_origen_id = origen.id" in sql
    assert "origen.anio_lectivo_id = %s" in sql
    assert "destino.anio_lectivo_id = %s" in sql
    assert params == (3, 1, 2)
    assert filas[0]["tipo_pago_destino_id"] == 40


def test_el_valor_copiado_conserva_importe_motivo_y_estado():
    cursor = CursorFalso(una=[(91,)])
    valor = {
        "tipo_pago_destino_id": 40,
        "valor": 180000,
        "motivo": "Beca parcial",
        "activo": False,
    }

    valor_id = getattr(repositorio, "insertar_valor_especial_copiado")(
        cursor, 1, valor
    )

    sql, params = cursor.consultas[0]
    assert valor_id == 91
    assert "INSERT INTO tipos_pagos_estudiantes" in sql
    assert params == (40, 1, 180000, "Beca parcial", False)
