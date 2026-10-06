"""Fase 5.4: copia transaccional de la configuración del año activo.

Todo se prueba con dobles. Estas pruebas no crean años ni datos en una base
real y no ejecutan migraciones.
"""
from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from psycopg2 import IntegrityError

from app.controllers import anios_lectivos_controller as controlador
from app.repositories import anios_lectivos_repository as repositorio
from app.routes import anios_lectivos as rutas


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


def _opciones(**cambios):
    valores = {
        "copiar_precios": False,
        "copiar_carga_academica": False,
        "copiar_directores": False,
    }
    valores.update(cambios)
    return SimpleNamespace(**valores)


@pytest.fixture
def entorno_copia(monkeypatch):
    estado = SimpleNamespace(
        activo=(2, 2026, "activo"),
        destino=(3, 2027, "preparacion"),
        choque_curso=None,
        choque_concepto=None,
        cursos=[
            {
                "id": 1,
                "nombre": "PRIMERO A",
                "jornada": "Mañana",
                "nivel": "primaria",
                "director_grupo_id": 7,
            },
            {
                "id": 2,
                "nombre": "SEGUNDO A",
                "jornada": "Mañana",
                "nivel": "primaria",
                "director_grupo_id": None,
            },
        ],
        conceptos=[
            {"id": 10, "nombre": "MATRICULA"},
            {"id": 11, "nombre": "MENSUALIDAD"},
        ],
        precios=[
            {
                "tipo_pago_id": 11,
                "curso_id": 1,
                "valor": 200000,
                "activo": True,
            }
        ],
        asignaciones=[
            {
                "id": 41,
                "curso_id": 1,
                "materia_id": 5,
                "profesor_id": 8,
                "dia": "Lunes",
                "horas": 2,
                "hora_inicio": "07:00",
                "hora_fin": "08:00",
                "activo": True,
                "asignacion_academica_id": 41,
                "orden_boletin": 1,
            },
            {
                "id": 42,
                "curso_id": 1,
                "materia_id": 5,
                "profesor_id": 8,
                "dia": "Miércoles",
                "horas": 2,
                "hora_inicio": "07:00",
                "hora_fin": "08:00",
                "activo": True,
                "asignacion_academica_id": 41,
                "orden_boletin": 1,
            },
        ],
        eventos=[],
        commits=0,
        rollbacks=0,
        fallar_curso_id=None,
        fallar_concepto_id=None,
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

    def activo(cursor_recibido):
        estado.eventos.append(("activo", cursor_recibido is cursor))
        return estado.activo

    def destino(cursor_recibido, anio_id):
        estado.eventos.append(("destino", cursor_recibido is cursor, anio_id))
        return estado.destino

    def choque_curso(cursor_recibido, origen_id, destino_id):
        estado.eventos.append(("choque_curso", origen_id, destino_id))
        return estado.choque_curso

    def choque_concepto(cursor_recibido, origen_id, destino_id):
        estado.eventos.append(("choque_concepto", origen_id, destino_id))
        return estado.choque_concepto

    def cursos(cursor_recibido, origen_id):
        estado.eventos.append(("lista_cursos", origen_id))
        return estado.cursos

    def insertar_curso(cursor_recibido, curso, destino_id, copiar_director):
        estado.eventos.append(
            ("inserta_curso", curso["id"], destino_id, copiar_director)
        )
        if curso["id"] == estado.fallar_curso_id:
            raise IntegrityError("curso duplicado")
        return 1000 + curso["id"]

    def conceptos(cursor_recibido, origen_id):
        estado.eventos.append(("lista_conceptos", origen_id))
        return estado.conceptos

    def insertar_concepto(cursor_recibido, concepto, destino_id):
        estado.eventos.append(("inserta_concepto", concepto["id"], destino_id))
        if concepto["id"] == estado.fallar_concepto_id:
            raise IntegrityError("concepto duplicado")
        return 2000 + concepto["id"]

    def precios(cursor_recibido, origen_id):
        estado.eventos.append(("lista_precios", origen_id))
        return estado.precios

    def insertar_precio(cursor_recibido, precio, tipo_id, curso_id):
        estado.eventos.append(
            (
                "inserta_precio",
                precio["tipo_pago_id"],
                precio["curso_id"],
                tipo_id,
                curso_id,
            )
        )
        return 1

    def asignaciones(cursor_recibido, origen_id):
        estado.eventos.append(("lista_asignaciones", origen_id))
        return estado.asignaciones

    def insertar_asignacion(cursor_recibido, asignacion, curso_id):
        estado.eventos.append(
            ("inserta_asignacion", asignacion["id"], curso_id)
        )
        return 3000 + asignacion["id"]

    def enlazar_asignacion(cursor_recibido, asignacion_id, cabecera_id):
        estado.eventos.append(("enlaza_asignacion", asignacion_id, cabecera_id))

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    dobles = {
        "leer_anio_activo_para_actualizar": activo,
        "leer_anio_lectivo_para_actualizar": destino,
        "buscar_choque_curso_para_copia": choque_curso,
        "buscar_choque_concepto_para_copia": choque_concepto,
        "listar_cursos_para_copiar": cursos,
        "insertar_curso_copiado": insertar_curso,
        "listar_conceptos_para_copiar": conceptos,
        "insertar_concepto_copiado": insertar_concepto,
        "listar_precios_para_copiar": precios,
        "insertar_precio_copiado": insertar_precio,
        "listar_asignaciones_para_copiar": asignaciones,
        "insertar_asignacion_copiada": insertar_asignacion,
        "enlazar_asignacion_academica_copiada": enlazar_asignacion,
    }
    for nombre, doble in dobles.items():
        monkeypatch.setattr(
            controlador.anios_lectivos_repository,
            nombre,
            doble,
            raising=False,
        )
    return estado


def test_las_opciones_son_explicitas_y_seguras_por_defecto():
    opciones = rutas.CopiarConfiguracionAnio()

    assert opciones.model_dump() == {
        "copiar_precios": False,
        "copiar_carga_academica": False,
        "copiar_directores": False,
    }


def test_la_copia_basica_siempre_incluye_cursos_y_conceptos(entorno_copia):
    respuesta = controlador.copiar_configuracion_anio_controller(3, _opciones())

    assert respuesta == {
        "anio_origen_id": 2,
        "anio_origen": 2026,
        "anio_destino_id": 3,
        "anio_destino": 2027,
        "copiados": {
            "cursos": 2,
            "conceptos_pago": 2,
            "precios_curso": 0,
            "asignaciones": 0,
            "directores_grupo": 0,
        },
    }
    assert ("inserta_curso", 1, 3, False) in entorno_copia.eventos
    assert ("inserta_concepto", 10, 3) in entorno_copia.eventos
    assert not any(e[0] == "lista_precios" for e in entorno_copia.eventos)
    assert not any(e[0] == "lista_asignaciones" for e in entorno_copia.eventos)
    assert entorno_copia.commits == 1
    assert entorno_copia.rollbacks == 0


def test_la_copia_completa_rehace_mapeos_y_referencias(entorno_copia):
    respuesta = controlador.copiar_configuracion_anio_controller(
        3,
        _opciones(
            copiar_precios=True,
            copiar_carga_academica=True,
            copiar_directores=True,
        ),
    )

    assert respuesta["copiados"] == {
        "cursos": 2,
        "conceptos_pago": 2,
        "precios_curso": 1,
        "asignaciones": 2,
        "directores_grupo": 1,
    }
    assert ("inserta_precio", 11, 1, 2011, 1001) in entorno_copia.eventos
    assert ("inserta_asignacion", 41, 1001) in entorno_copia.eventos
    assert ("inserta_asignacion", 42, 1001) in entorno_copia.eventos
    assert ("enlaza_asignacion", 3041, 3041) in entorno_copia.eventos
    assert ("enlaza_asignacion", 3042, 3041) in entorno_copia.eventos
    assert not any(
        e[0] == "enlaza_asignacion" and e[2] in {41, 42}
        for e in entorno_copia.eventos
    )


@pytest.mark.parametrize(
    ("destino", "mensaje"),
    [
        ((3, 2027, "activo"), "preparación"),
        ((3, 2028, "preparacion"), "2027"),
    ],
)
def test_el_destino_debe_ser_el_siguiente_y_estar_en_preparacion(
    entorno_copia, destino, mensaje
):
    entorno_copia.destino = destino

    with pytest.raises(controlador.AnioLectivoDestinoInvalidoError) as error:
        controlador.copiar_configuracion_anio_controller(3, _opciones())

    assert mensaje in str(error.value)
    assert not any(e[0] == "inserta_curso" for e in entorno_copia.eventos)
    assert entorno_copia.commits == 0
    assert entorno_copia.rollbacks == 1


def test_un_destino_inexistente_responde_como_anio_inexistente(entorno_copia):
    entorno_copia.destino = None

    with pytest.raises(controlador.AnioLectivoInexistenteError):
        controlador.copiar_configuracion_anio_controller(99, _opciones())

    assert entorno_copia.rollbacks == 1


def test_un_curso_ya_existente_identifica_el_choque_y_no_copia(entorno_copia):
    entorno_copia.choque_curso = ("PRIMERO A", "Mañana")

    with pytest.raises(controlador.ConfiguracionAnioDuplicadaError) as error:
        controlador.copiar_configuracion_anio_controller(3, _opciones())

    assert "PRIMERO A" in str(error.value)
    assert "Mañana" in str(error.value)
    assert not any(e[0].startswith("inserta_") for e in entorno_copia.eventos)
    assert entorno_copia.rollbacks == 1


def test_un_concepto_ya_existente_identifica_el_choque_y_no_copia(entorno_copia):
    entorno_copia.choque_concepto = ("MATRICULA",)

    with pytest.raises(controlador.ConfiguracionAnioDuplicadaError) as error:
        controlador.copiar_configuracion_anio_controller(3, _opciones())

    assert "MATRICULA" in str(error.value)
    assert "concepto" in str(error.value).lower()
    assert not any(e[0].startswith("inserta_") for e in entorno_copia.eventos)
    assert entorno_copia.rollbacks == 1


def test_un_choque_concurrente_identifica_el_curso_y_revierte_todo(entorno_copia):
    entorno_copia.fallar_curso_id = 2

    with pytest.raises(controlador.ConfiguracionAnioDuplicadaError) as error:
        controlador.copiar_configuracion_anio_controller(3, _opciones())

    assert "SEGUNDO A" in str(error.value)
    assert entorno_copia.commits == 0
    assert entorno_copia.rollbacks == 1


def test_un_choque_concurrente_identifica_el_concepto_y_revierte_todo(
    entorno_copia,
):
    entorno_copia.fallar_concepto_id = 11

    with pytest.raises(controlador.ConfiguracionAnioDuplicadaError) as error:
        controlador.copiar_configuracion_anio_controller(3, _opciones())

    assert "MENSUALIDAD" in str(error.value)
    assert entorno_copia.commits == 0
    assert entorno_copia.rollbacks == 1


def test_un_precio_sin_copia_de_curso_o_concepto_revierte(entorno_copia):
    entorno_copia.precios[0]["curso_id"] = 999

    with pytest.raises(controlador.ConfiguracionAnioInconsistenteError) as error:
        controlador.copiar_configuracion_anio_controller(
            3, _opciones(copiar_precios=True)
        )

    assert "precio" in str(error.value).lower()
    assert entorno_copia.rollbacks == 1


def test_una_cabecera_academica_ajena_a_la_copia_revierte(entorno_copia):
    entorno_copia.asignaciones[1]["asignacion_academica_id"] = 999

    with pytest.raises(controlador.ConfiguracionAnioInconsistenteError) as error:
        controlador.copiar_configuracion_anio_controller(
            3, _opciones(copiar_carga_academica=True)
        )

    assert "asignación" in str(error.value).lower()
    assert entorno_copia.rollbacks == 1


def test_la_ruta_traduce_los_choques_a_409(monkeypatch):
    def copiar_falso(_anio_id, _opciones):
        raise controlador.ConfiguracionAnioDuplicadaError("Curso repetido")

    monkeypatch.setattr(rutas, "copiar_configuracion_anio_controller", copiar_falso)

    with pytest.raises(HTTPException) as error:
        rutas.copiar_configuracion_anio(3, rutas.CopiarConfiguracionAnio())

    assert error.value.status_code == 409
    assert error.value.detail == "Curso repetido"


def test_la_ruta_de_copia_exige_admin():
    from app.dependencies import get_current_active_admin

    ruta = next(
        ruta
        for ruta in rutas.router.routes
        if ruta.path == "/anios-lectivos/{anio_lectivo_id}/copiar-configuracion"
    )

    assert get_current_active_admin in [
        dependencia.call for dependencia in ruta.dependant.dependencies
    ]


# ---------------------------------------------------------------------------
# SQL del repositorio: campos copiados y referencias de origen.
# ---------------------------------------------------------------------------


def test_el_curso_copiado_nace_activo_y_guarda_su_origen():
    cursor = CursorFalso(una=[(101,)])
    curso = {
        "id": 1,
        "nombre": "PRIMERO A",
        "jornada": "Mañana",
        "nivel": "primaria",
        "director_grupo_id": 7,
    }

    nuevo_id = repositorio.insertar_curso_copiado(cursor, curso, 3, False)

    sql, params = cursor.consultas[0]
    assert nuevo_id == 101
    assert "nombre, jornada, estado, nivel, director_grupo_id" in sql
    assert "anio_lectivo_id, curso_origen_id" in sql
    assert "VALUES (%s, %s, 'activo', %s, %s, %s, %s)" in sql
    assert params == ("PRIMERO A", "Mañana", "primaria", None, 3, 1)


def test_solo_se_listan_para_copia_los_cursos_activos_del_origen():
    cursor = CursorFalso(
        todas=[[(1, "PRIMERO A", "Mañana", "primaria", 7)]]
    )

    cursos = repositorio.listar_cursos_para_copiar(cursor, 2)

    sql, params = cursor.consultas[0]
    assert cursos == [
        {
            "id": 1,
            "nombre": "PRIMERO A",
            "jornada": "Mañana",
            "nivel": "primaria",
            "director_grupo_id": 7,
        }
    ]
    assert "COALESCE(LOWER(estado), 'activo') = 'activo'" in sql
    assert params == (2,)


def test_el_concepto_copia_toda_su_configuracion_y_guarda_su_origen():
    cursor = CursorFalso(una=[(210,)])
    concepto = {
        "id": 10,
        "nombre": "MATRICULA",
        "valor": 300000,
        "descripcion": "Matrícula anual",
        "tipo_cobro": "anual",
        "fecha_limite": date(2026, 12, 15),
        "dia_limite_mes": 5,
        "dias_gracia": 2,
        "mora_tipo": "fijo",
        "mora_valor": 10000,
        "mes_inicial": 2,
        "mes_final": 12,
        "frecuencia_meses": 1,
        "generacion_automatica": False,
        "activo": False,
    }

    nuevo_id = repositorio.insertar_concepto_copiado(cursor, concepto, 3)

    sql, params = cursor.consultas[0]
    assert nuevo_id == 210
    for columna in (
        "descripcion",
        "tipo_cobro",
        "fecha_limite",
        "dia_limite_mes",
        "dias_gracia",
        "mora_tipo",
        "mora_valor",
        "mes_inicial",
        "mes_final",
        "frecuencia_meses",
        "generacion_automatica",
        "activo",
        "tipo_pago_origen_id",
    ):
        assert columna in sql
    assert params[-2:] == (3, 10)
    assert params[2] == "Matrícula anual"
    assert params[13] is False


def test_la_asignacion_copia_horario_estado_y_orden_sin_origen_viejo():
    cursor = CursorFalso(una=[(341,)])
    asignacion = {
        "id": 41,
        "curso_id": 1,
        "materia_id": 5,
        "profesor_id": 8,
        "dia": "Lunes",
        "horas": 2,
        "hora_inicio": "07:00",
        "hora_fin": "08:00",
        "activo": False,
        "asignacion_academica_id": 41,
        "orden_boletin": 3,
    }

    nuevo_id = repositorio.insertar_asignacion_copiada(cursor, asignacion, 101)

    sql, params = cursor.consultas[0]
    assert nuevo_id == 341
    assert "horas" in sql
    assert "activo" in sql
    assert "orden_boletin" in sql
    assert "asignacion_academica_id" not in sql
    assert params == (101, 5, 8, "Lunes", 2, "07:00", "08:00", False, 3)


def test_el_enlace_academico_solo_apunta_a_ids_nuevos():
    cursor = CursorFalso()

    repositorio.enlazar_asignacion_academica_copiada(cursor, 342, 341)

    sql, params = cursor.consultas[0]
    assert "SET asignacion_academica_id = %s" in sql
    assert "WHERE id = %s" in sql
    assert params == (341, 342)


def test_el_precio_copiado_usa_los_ids_nuevos_y_conserva_su_estado():
    cursor = CursorFalso(una=[(501,)])
    precio = {"valor": 225000, "activo": False}

    nuevo_id = repositorio.insertar_precio_copiado(cursor, precio, 210, 101)

    sql, params = cursor.consultas[0]
    assert nuevo_id == 501
    assert "tipo_pago_id, curso_id, valor, activo" in sql
    assert params == (210, 101, 225000, False)
