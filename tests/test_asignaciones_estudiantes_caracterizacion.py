"""Caracterizacion de asignaciones y estudiantes, subcapa 6.0.

Fija el comportamiento observable ANTES de cualquier extraccion de la capa 6.
No corrige nada: describe lo que el codigo hace hoy, incluidas sus rarezas.

Lo que mas importa aqui no son los payloads sino tres reglas que protegen el
historial academico y que hoy no tenian ninguna prueba:

1. `asignacion_tiene_historial` impide cambiar profesor, curso o materia de una
   asignacion que ya tiene notas, asistencia, boletines u observaciones. Es la
   regla que evita reescribir el pasado academico de un estudiante.
2. Ni desactivar una asignacion ni desactivar un estudiante borran filas: ambos
   caminos hacen UPDATE, nunca DELETE. Las 7 claves foraneas que apuntan a
   `asignaciones` y las 9 que apuntan a `estudiantes` hacen que un borrado real
   fuese destructivo o imposible.
3. `obtener_detalles_estudiante_controller` degrada por secciones: si una
   consulta falla, revierte y sigue con las demas en vez de tumbar la respuesta.

Los conteos de consultas se fijan porque una extraccion que agrupe o repita
lecturas los cambiaria en silencio.
"""

import ast
from pathlib import Path

import pytest
from psycopg2 import IntegrityError, errorcodes

from app.controllers import asignacion_controller, estudiante_controller
from app.schemas.asignacion import AsignacionCreate, AsignacionEdit, OrdenBoletinUpdate


class CursorEspia:
    """Cursor doble que registra cada execute y sirve respuestas en orden."""

    def __init__(self, una=None, todas=None, description=None, fallar_si=None):
        self.ejecutadas = []
        self._una = list(una or [])
        self._todas = list(todas or [])
        self.description = description
        self._fallar_si = fallar_si
        self.cerrado = False

    def execute(self, query, params=None):
        self.ejecutadas.append((query, params))
        if self._fallar_si is not None:
            self._fallar_si(query)

    def fetchone(self):
        return self._una.pop(0) if self._una else None

    def fetchall(self):
        return self._todas.pop(0) if self._todas else []

    def close(self):
        self.cerrado = True

    @property
    def sql(self):
        return [query for query, _ in self.ejecutadas]

    @property
    def parametros(self):
        return [params for _, params in self.ejecutadas]


class ConexionEspia:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False

    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


class UniqueViolation(IntegrityError):
    """IntegrityError con el pgcode que el controlador traduce a 409."""

    pgcode = errorcodes.UNIQUE_VIOLATION


@pytest.fixture
def conexion_de(monkeypatch):
    """Instala una conexion doble en el modulo indicado."""

    def instalar(modulo, **kwargs):
        cursor = CursorEspia(**kwargs)
        conn = ConexionEspia(cursor)
        monkeypatch.setattr(modulo, "get_connection", lambda: conn)
        return cursor, conn

    return instalar


@pytest.fixture
def cursor_de(monkeypatch):
    """Instala un get_cursor doble y registra el commit pedido."""

    from contextlib import contextmanager

    def instalar(modulo, **kwargs):
        cursor = CursorEspia(**kwargs)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(modulo, "get_cursor", fake_get_cursor)
        return cursor, commits

    return instalar


def _asignacion(**overrides):
    datos = {
        "profesor_id": 9,
        "curso_id": 4,
        "materia_id": 3,
        "dia": "Lunes",
        "hora_inicio": "08:00",
        "hora_fin": "09:00",
    }
    datos.update(overrides)
    return AsignacionCreate(**datos)


def _asignacion_edit(**overrides):
    datos = {
        "profesor_id": 9,
        "curso_id": 4,
        "materia_id": 3,
        "dia": "Lunes",
        "hora_inicio": "08:00",
        "hora_fin": "09:00",
    }
    datos.update(overrides)
    return AsignacionEdit(**datos)


# ---------------------------------------------------------------------------
# Asignaciones: alta
# ---------------------------------------------------------------------------


def test_asignar_profesor_camino_feliz_cuesta_doce_consultas(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        una=[
            (1,),          # profesor_activo
            (1,),          # curso_activo
            (1,),          # materia_activa
            None,          # validar_profesor_responsable_materia: nadie mas
            None,          # validar_horario_unico: no duplicado
            None,          # obtener_asignacion_academica_id: primera del grupo
            (100,),        # obtener_orden_boletin_materia_curso
            ("Mañana",),   # validar_jornada_curso
            (77,),         # INSERT ... RETURNING id
        ],
        todas=[[], []],    # cruce por profesor y por curso
    )

    respuesta = asignacion_controller.asignar_profesor_controller(_asignacion())

    assert respuesta == {"mensaje": "Asignación creada", "id": 77}
    assert len(cursor.ejecutadas) == 12
    assert conn.commits == 1
    assert conn.cerrada is True
    assert cursor.cerrado is True


def test_asignar_profesor_primera_del_grupo_se_apunta_a_si_misma(conexion_de):
    cursor, _ = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, None, None, (100,), ("Mañana",), (77,)],
        todas=[[], []],
    )

    asignacion_controller.asignar_profesor_controller(_asignacion())

    ultima_sql, ultimos_params = cursor.ejecutadas[-1]
    assert "SET asignacion_academica_id = id" in ultima_sql
    assert ultimos_params == (77,)


def test_asignar_profesor_hereda_la_asignacion_academica_existente(conexion_de):
    cursor, _ = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, None, (5,), (100,), ("Mañana",), (77,)],
        todas=[[], []],
    )

    asignacion_controller.asignar_profesor_controller(_asignacion())

    # Sin UPDATE de autorreferencia: hereda el 5 y ahorra una consulta.
    assert len(cursor.ejecutadas) == 11
    insert_sql, insert_params = cursor.ejecutadas[-1]
    assert "INSERT INTO asignaciones" in insert_sql
    assert insert_params[6] == 5
    assert insert_params[7] == 100


def test_asignar_profesor_traduce_unique_violation_a_duplicada(conexion_de):
    def fallar(query):
        if "INSERT INTO asignaciones" in query:
            raise UniqueViolation("duplicado")

    cursor, conn = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, None, None, (100,), ("Mañana",)],
        todas=[[], []],
        fallar_si=fallar,
    )

    with pytest.raises(asignacion_controller.AsignacionDuplicadaError) as exc:
        asignacion_controller.asignar_profesor_controller(_asignacion())

    assert str(exc.value) == asignacion_controller.ASIGNACION_OTRO_PROFESOR_MENSAJE
    assert conn.rollbacks == 1
    assert conn.commits == 0
    assert conn.cerrada is True


def test_asignar_profesor_rechaza_materia_de_otro_profesor(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), ("Ana Ríos",)],
    )

    with pytest.raises(asignacion_controller.AsignacionDuplicadaError) as exc:
        asignacion_controller.asignar_profesor_controller(_asignacion())

    assert "Ana Ríos" in str(exc.value)
    assert conn.commits == 0
    assert len(cursor.ejecutadas) == 4


def test_asignar_profesor_rechaza_horario_identico_repetido(conexion_de):
    _, conn = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, (1,)],
    )

    with pytest.raises(asignacion_controller.AsignacionDuplicadaError) as exc:
        asignacion_controller.asignar_profesor_controller(_asignacion())

    assert str(exc.value) == asignacion_controller.ASIGNACION_HORARIO_DUPLICADO_MENSAJE
    assert conn.commits == 0


def test_asignar_profesor_detecta_cruce_del_profesor(conexion_de):
    _, conn = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, None, None, (100,), ("Mañana",)],
        todas=[[("08:30", "09:30")]],
    )

    respuesta = asignacion_controller.asignar_profesor_controller(_asignacion())

    assert respuesta == {
        "error": "Error: El profesor ya tiene una clase asignada en ese horario y ese día."
    }
    assert conn.commits == 0


def test_asignar_profesor_detecta_cruce_del_curso(conexion_de):
    _, conn = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, None, None, (100,), ("Mañana",)],
        todas=[[], [("08:30", "09:30")]],
    )

    respuesta = asignacion_controller.asignar_profesor_controller(_asignacion())

    assert respuesta == {
        "error": "Error: El curso (salón) ya tiene otra clase asignada en ese horario y ese día."
    }
    assert conn.commits == 0


def test_asignar_profesor_respeta_la_jornada_del_curso(conexion_de):
    _, conn = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, None, None, (100,), ("Mañana",)],
    )

    # 13:00-14:00 es una franja institucional valida —cae entera en la jornada
    # Tarde— pero el curso es de manana, y esa regla la impone el curso.
    respuesta = asignacion_controller.asignar_profesor_controller(
        _asignacion(hora_inicio="13:00", hora_fin="14:00")
    )

    assert respuesta == {
        "error": "El curso es jornada Mañana: la clase debe terminar antes o a las 12:30."
    }
    assert conn.commits == 0


def test_asignar_profesor_sin_horario_omite_las_validaciones_de_cruce(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        una=[(1,), (1,), (1,), None, None, (100,), (77,)],
    )

    respuesta = asignacion_controller.asignar_profesor_controller(
        _asignacion(dia=None, hora_inicio=None, hora_fin=None)
    )

    assert respuesta == {"mensaje": "Asignación creada", "id": 77}
    # Sin horario, validar_horario_unico sale sin consultar y no hay jornada ni
    # los dos cruces: 12 - 4 = 8 consultas.
    assert len(cursor.ejecutadas) == 8
    assert conn.commits == 1


# ---------------------------------------------------------------------------
# Asignaciones: el historial academico es lo que no se puede romper
# ---------------------------------------------------------------------------


def test_editar_bloquea_el_cambio_academico_si_ya_hay_historial(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        una=[
            (9, 4, 3, True, 7),  # estado actual
            (1,),                # profesor_activo
            (1,),                # curso_activo
            (1,),                # materia_activa
            (1,),                # plan_de_clases tiene columna asignacion_id
            (1,),                # y tiene al menos una fila
        ],
    )

    respuesta = asignacion_controller.editar_asignacion_controller(
        55, _asignacion_edit(materia_id=99)
    )

    assert respuesta == {
        "error": (
            "Esta asignación ya tiene historial académico. "
            "Desactívala y crea una nueva para cambiar profesor, curso o materia."
        )
    }
    assert conn.commits == 0
    assert len(cursor.ejecutadas) == 6
    assert not any("UPDATE asignaciones" in sql for sql in cursor.sql)


def test_asignacion_tiene_historial_recorre_las_siete_tablas():
    cursor = CursorEspia(una=[None] * 14)

    assert asignacion_controller.asignacion_tiene_historial(cursor, 55) is False

    consultadas = [
        params[0]
        for sql, params in cursor.ejecutadas
        if "information_schema.columns" in sql
    ]
    assert consultadas == [
        "plan_de_clases",
        "planeador_anual",
        "asistencia",
        "notas",
        "notas_detalle",
        "boletin_cabecera",
        "observaciones",
    ]
    # Ninguna tabla tiene la columna, asi que no se consulta ninguna fila.
    assert len(cursor.ejecutadas) == 7


def test_asignacion_tiene_historial_omite_tablas_sin_la_columna():
    # La columna existe solo en la primera tabla y no hay filas en ella.
    cursor = CursorEspia(una=[(1,), None] + [None] * 6)

    assert asignacion_controller.asignacion_tiene_historial(cursor, 55) is False

    assert len(cursor.ejecutadas) == 8
    assert "FROM plan_de_clases" in cursor.sql[1]


def test_editar_permite_cambiar_solo_el_horario_con_historial(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        una=[
            (9, 4, 3, True, 7),  # misma relacion academica
            (1,), (1,), (1,),
            None,                # responsable
            None,                # horario unico
            ("Mañana",),         # jornada
            (55,),               # UPDATE ... RETURNING id
        ],
        todas=[[], []],
    )

    respuesta = asignacion_controller.editar_asignacion_controller(
        55, _asignacion_edit(hora_inicio="10:00", hora_fin="11:00")
    )

    assert respuesta == {"mensaje": "Asignación actualizada"}
    assert conn.commits == 1
    assert len(cursor.ejecutadas) == 10
    # No se consulta el historial porque la relacion academica no cambia.
    assert not any("information_schema.columns" in sql for sql in cursor.sql)
    update_sql, update_params = cursor.ejecutadas[-1]
    assert "UPDATE asignaciones" in update_sql
    assert "AND activo = TRUE" in update_sql
    assert update_params[6] == 7  # conserva la asignacion academica actual


def test_editar_rechaza_una_asignacion_inactiva(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        una=[(9, 4, 3, False, 7)],
    )

    respuesta = asignacion_controller.editar_asignacion_controller(55, _asignacion_edit())

    assert respuesta == {"error": "No se puede editar una asignación inactiva."}
    assert len(cursor.ejecutadas) == 1
    assert conn.commits == 0


def test_editar_asignacion_inexistente_no_toca_nada(conexion_de):
    cursor, conn = conexion_de(asignacion_controller, una=[None])

    respuesta = asignacion_controller.editar_asignacion_controller(55, _asignacion_edit())

    assert respuesta == {"error": "Asignación no encontrada"}
    assert len(cursor.ejecutadas) == 1
    assert conn.commits == 0


def test_desactivar_por_id_nunca_borra_filas(conexion_de):
    cursor, conn = conexion_de(asignacion_controller, una=[(55,)])

    respuesta = asignacion_controller.eliminar_asignacion_por_id_controller(55)

    assert respuesta == {
        "mensaje": "Asignación desactivada. El historial académico se conserva."
    }
    sql_completo = "\n".join(cursor.sql).upper()
    assert "DELETE" not in sql_completo
    assert "SET ACTIVO = FALSE" in sql_completo
    assert conn.commits == 1


# ---------------------------------------------------------------------------
# Asignaciones: orden del boletin
# ---------------------------------------------------------------------------


def test_orden_boletin_reinicia_a_cien_y_luego_numera(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        una=[(1,)],
        todas=[[(3,), (5,)], []],
    )

    respuesta = asignacion_controller.actualizar_orden_boletin_curso_controller(
        4, OrdenBoletinUpdate(materias=[{"materia_id": 5}, {"materia_id": 3}])
    )

    assert respuesta["mensaje"] == "Orden del boletín actualizado"
    assert respuesta["curso_id"] == 4
    updates = [
        (sql, params) for sql, params in cursor.ejecutadas if "SET orden_boletin" in sql
    ]
    assert len(updates) == 3
    assert updates[0][1] == (4,)          # reinicio masivo a 100
    assert updates[1][1] == (1, 4, 5)     # primera posicion: materia 5
    assert updates[2][1] == (2, 4, 3)     # segunda posicion: materia 3
    assert conn.commits == 1
    # Curso activo, materias asignadas, reinicio, dos posiciones y relectura:
    # el coste crece con el numero de materias reordenadas.
    assert len(cursor.ejecutadas) == 6


def test_orden_boletin_rechaza_materias_repetidas(conexion_de):
    cursor, conn = conexion_de(asignacion_controller, una=[(1,)])

    respuesta = asignacion_controller.actualizar_orden_boletin_curso_controller(
        4, OrdenBoletinUpdate(materias=[{"materia_id": 5}, {"materia_id": 5}])
    )

    assert respuesta == {"error": "El orden enviado contiene materias repetidas."}
    assert len(cursor.ejecutadas) == 1
    assert conn.commits == 0


def test_orden_boletin_rechaza_materias_no_asignadas(conexion_de):
    _, conn = conexion_de(
        asignacion_controller,
        una=[(1,)],
        todas=[[(3,)]],
    )

    respuesta = asignacion_controller.actualizar_orden_boletin_curso_controller(
        4, OrdenBoletinUpdate(materias=[{"materia_id": 99}])
    )

    assert respuesta == {
        "error": "El orden contiene materias que no están asignadas a este curso."
    }
    assert conn.commits == 0


def test_orden_boletin_rechaza_curso_inactivo(conexion_de):
    cursor, conn = conexion_de(asignacion_controller, una=[None])

    respuesta = asignacion_controller.actualizar_orden_boletin_curso_controller(
        4, OrdenBoletinUpdate(materias=[{"materia_id": 5}])
    )

    assert respuesta == {"error": "Curso no encontrado o inactivo."}
    assert len(cursor.ejecutadas) == 1
    assert conn.commits == 0


def test_consultar_orden_boletin_agrupa_por_materia(conexion_de):
    cursor, conn = conexion_de(
        asignacion_controller,
        todas=[[(7, 4, "Quinto A", 3, "Matemáticas", 9, "Ana Ríos", 1, 2)]],
    )

    respuesta = asignacion_controller.obtener_orden_boletin_curso_controller(4)

    assert respuesta == {
        "curso_id": 4,
        "items": [
            {
                "asignacion_academica_id": 7,
                "curso_id": 4,
                "curso_nombre": "Quinto A",
                "materia_id": 3,
                "materia_nombre": "Matemáticas",
                "profesor_id": 9,
                "profesor_nombre": "Ana Ríos",
                "orden_boletin": 1,
                "horarios": 2,
            }
        ],
    }
    assert len(cursor.ejecutadas) == 1
    assert conn.commits == 0


# ---------------------------------------------------------------------------
# Estudiantes
# ---------------------------------------------------------------------------


def test_obtener_estudiante_por_id_devuelve_todas_las_columnas(conexion_de):
    cursor, conn = conexion_de(
        estudiante_controller,
        una=[(55, "Ana", "2010-05-01", None, "2.5")],
        description=[
            ("id",), ("nombre",), ("fecha_nacimiento",), ("estado",),
            ("descuento_matricula",),
        ],
    )

    respuesta = estudiante_controller.obtener_estudiante_por_id_controller(55)

    # El SELECT * hace que el contrato sea el schema entero de la tabla.
    assert cursor.sql[0] == "SELECT * FROM estudiantes WHERE id = %s"
    assert respuesta == {
        "id": 55,
        "nombre": "Ana",
        "fecha_nacimiento": "2010-05-01",
        "estado": "activo",
        "descuento_matricula": 2.5,
    }
    assert conn.commits == 0
    assert conn.cerrada is True


def test_obtener_estudiante_por_id_normaliza_el_estado_guardado(conexion_de):
    conexion_de(
        estudiante_controller,
        una=[(55, "  RETIRADO  ")],
        description=[("id",), ("estado",)],
    )

    respuesta = estudiante_controller.obtener_estudiante_por_id_controller(55)

    assert respuesta["estado"] == "retirado"


def test_obtener_estudiante_inexistente_devuelve_none(conexion_de):
    _, conn = conexion_de(estudiante_controller, una=[None])

    assert estudiante_controller.obtener_estudiante_por_id_controller(999) is None
    assert conn.cerrada is True


def test_actualizar_estado_confirma_y_devuelve_el_estado_normalizado(conexion_de):
    cursor, conn = conexion_de(estudiante_controller, una=[(55, "retirado")])

    respuesta = estudiante_controller.actualizar_estado_estudiante_controller(55, "RETIRADO")

    assert respuesta == {
        "mensaje": "Estado de estudiante actualizado",
        "id": 55,
        "estado": "retirado",
    }
    assert cursor.parametros[0] == ("retirado", 55)
    assert "SET estado = %s" in cursor.sql[0]
    assert "DELETE" not in "\n".join(cursor.sql).upper()
    assert conn.commits == 1
    assert conn.rollbacks == 0


def test_actualizar_estado_de_estudiante_inexistente_revierte(conexion_de):
    _, conn = conexion_de(estudiante_controller, una=[None])

    respuesta = estudiante_controller.actualizar_estado_estudiante_controller(999, "activo")

    assert respuesta == {"error": "Estudiante no encontrado"}
    assert conn.rollbacks == 1
    assert conn.commits == 0


def test_actualizar_estado_rechaza_un_estado_desconocido():
    with pytest.raises(ValueError, match="Estado de estudiante invalido"):
        estudiante_controller.actualizar_estado_estudiante_controller(55, "expulsado")


def test_listar_estudiantes_filtra_por_estado_activo_por_defecto(conexion_de):
    cursor, conn = conexion_de(
        estudiante_controller,
        todas=[[(55, "Ana", "Ríos", "123", None, 4, "a@b.c", "activo")]],
    )

    respuesta = estudiante_controller.obtener_estudiantes_controller()

    assert "COALESCE(LOWER(estado), 'activo') = %s" in cursor.sql[0]
    assert cursor.parametros[0] == ("activo",)
    assert "ORDER BY apellido ASC, nombre ASC" in cursor.sql[0]
    assert respuesta == [
        {
            "id": 55,
            "nombre": "Ana",
            "apellido": "Ríos",
            "documento": "123",
            "fecha_nacimiento": None,
            "curso_id": 4,
            "email": "a@b.c",
            "estado": "activo",
        }
    ]
    assert conn.commits == 0


def test_listar_estudiantes_con_todos_no_filtra(conexion_de):
    cursor, _ = conexion_de(estudiante_controller, todas=[[]])

    estudiante_controller.obtener_estudiantes_controller(estado="todos")

    assert "WHERE" not in cursor.sql[0]
    assert cursor.parametros[0] == ()


def test_paginado_de_estudiantes_cuesta_dos_consultas(conexion_de):
    cursor, conn = conexion_de(
        estudiante_controller,
        una=[(7,)],
        todas=[[(55, "Ana", "Ríos", "123", None, 4, "a@b.c", "activo")]],
    )

    respuesta = estudiante_controller.obtener_estudiantes_paginado_controller(
        limit=10, offset=20, busqueda="ana"
    )

    assert len(cursor.ejecutadas) == 2
    assert "SELECT COUNT(*) FROM estudiantes" in cursor.sql[0]
    assert cursor.parametros[0] == ("activo", "%ana%", "%ana%", "%ana%")
    assert cursor.parametros[1] == ("activo", "%ana%", "%ana%", "%ana%", 10, 20)
    assert respuesta["total"] == 7
    assert respuesta["limit"] == 10
    assert respuesta["offset"] == 20
    assert len(respuesta["items"]) == 1
    assert conn.commits == 0


def test_deudas_de_estudiante_solo_devuelve_las_positivas(cursor_de, monkeypatch):
    cursor_de(estudiante_controller)
    monkeypatch.setattr(
        estudiante_controller,
        "calcular_deudas_estudiante",
        lambda cursor, est_id: {
            "curso_id": 4,
            "deudas": [
                {"concepto": "Pension", "deuda": 100},
                {"concepto": "Matricula", "deuda": 0},
            ],
        },
    )

    respuesta = estudiante_controller.obtener_deudas_estudiante_controller(55)

    assert respuesta == {
        "estudiante_id": 55,
        "curso_id": 4,
        "deudas": [{"concepto": "Pension", "deuda": 100}],
        "total_deuda": 100,
    }


def test_detalles_del_estudiante_cuesta_cuatro_consultas_propias(conexion_de, monkeypatch):
    cursor, conn = conexion_de(
        estudiante_controller,
        una=[(3,)],
        todas=[
            [("Matemáticas", 4.5)],
            [(1, "P1", "bien", "bien", "bien", "Matemáticas", "Ana Ríos")],
            [],
        ],
    )
    monkeypatch.setattr(
        estudiante_controller,
        "calcular_deudas_estudiante",
        lambda cursor, est_id: {"curso_id": 4, "deudas": []},
    )

    respuesta = estudiante_controller.obtener_detalles_estudiante_controller(55)

    # notas, inasistencias, observaciones e inventario: las deudas las cuenta cobros.
    assert len(cursor.ejecutadas) == 4
    assert respuesta["notas"] == [{"materia": "Matemáticas", "promedio": 4.5}]
    assert respuesta["promedio_general"] == 4.5
    assert respuesta["inasistencias"] == 3
    assert len(respuesta["observaciones"]) == 1
    assert respuesta["deudas"] == []
    assert "errores" not in respuesta
    assert conn.commits == 0
    assert conn.cerrada is True


def test_detalles_degrada_por_seccion_sin_tumbar_la_respuesta(conexion_de, monkeypatch):
    def fallar(query):
        if "notas_detalle" in query:
            raise RuntimeError("columna inexistente")

    cursor, conn = conexion_de(
        estudiante_controller,
        una=[(3,)],
        todas=[[], [], []],
        fallar_si=fallar,
    )
    monkeypatch.setattr(
        estudiante_controller,
        "calcular_deudas_estudiante",
        lambda cursor, est_id: {"curso_id": 4, "deudas": []},
    )

    respuesta = estudiante_controller.obtener_detalles_estudiante_controller(55)

    # La seccion rota revierte y se anota, pero las demas siguen respondiendo.
    assert respuesta["errores"] == {"notas": "No se pudo cargar esta seccion."}
    assert respuesta["notas"] == []
    assert respuesta["inasistencias"] == 3
    assert conn.rollbacks == 1
    assert conn.cerrada is True


def test_detalles_calcula_el_saldo_pendiente_del_inventario(conexion_de, monkeypatch):
    import datetime

    cursor, _ = conexion_de(
        estudiante_controller,
        una=[(0,)],
        todas=[
            [],
            [],
            [(12, datetime.date(2026, 3, 1), "Pendiente", "Uniforme", 1, 50.0, 20.0)],
        ],
    )
    monkeypatch.setattr(
        estudiante_controller,
        "calcular_deudas_estudiante",
        lambda cursor, est_id: {"curso_id": 4, "deudas": []},
    )

    respuesta = estudiante_controller.obtener_detalles_estudiante_controller(55)

    assert respuesta["productos_inventario"] == [
        {
            "venta_id": 12,
            "fecha": "2026-03-01",
            "estado": "Pendiente (Abonado)",
            "producto": "Uniforme",
            "cantidad": 1,
            "subtotal": 50.0,
            "saldo": 30.0,
        }
    ]


# ---------------------------------------------------------------------------
# Guardias estructurales
# ---------------------------------------------------------------------------


RAIZ_APP = Path(__file__).resolve().parents[1] / "app"


def _nombres_llamados(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    llamados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            objetivo = nodo.func
            if isinstance(objetivo, ast.Name):
                llamados.add(objetivo.id)
            elif isinstance(objetivo, ast.Attribute):
                llamados.add(objetivo.attr)
    return llamados


def test_obtener_clases_profesor_controller_sigue_sin_consumidores():
    """Documenta un hallazgo de 6.0: hay dos definiciones y ninguna se usa.

    `asignacion_controller` y `profesor_controller` definen cada uno una
    funcion con este nombre, y su SQL no coincide: la de profesor no filtra por
    `activo` ni por el estado del curso o la materia. La ruta /mis-clases no
    llama a ninguna de las dos, porque lleva su propio SQL inline.

    Esta prueba no exige retirarlas: fija que hoy estan muertas, para que quien
    decida borrarlas sepa que nada de produccion dependia de ellas y para que
    falle si alguien las conecta sin darse cuenta.
    """
    consumidores = [
        ruta
        for ruta in RAIZ_APP.rglob("*.py")
        if "obtener_clases_profesor_controller" in _nombres_llamados(ruta)
    ]

    assert consumidores == []


def test_las_escrituras_de_asignaciones_y_estudiantes_no_borran_filas():
    """Ni asignaciones ni estudiantes ejecutan DELETE: desactivan con UPDATE.

    Es lo que hace seguras las 7 claves foraneas que apuntan a `asignaciones` y
    las 9 que apuntan a `estudiantes`. Una extraccion que introdujera un DELETE
    romperia el historial academico o fallaria contra la clave foranea.
    """
    for nombre in ("asignacion_controller.py", "estudiante_controller.py"):
        codigo = (RAIZ_APP / "controllers" / nombre).read_text(encoding="utf-8")
        for nodo in ast.walk(ast.parse(codigo)):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                assert "DELETE FROM" not in nodo.value.upper(), nombre


def test_los_dominios_de_la_capa_6_no_tocan_archivos():
    """Verifica el supuesto que la activacion registro SIN comprobar.

    La bitacora anticipaba que estos dominios escribirian archivos via
    `app/services/storage.py`, y que por eso el rollback dejaria de ser
    reversible. No es cierto: solo branding y plan_de_clases usan storage.
    """
    for nombre in ("asignacion_controller.py", "estudiante_controller.py"):
        codigo = (RAIZ_APP / "controllers" / nombre).read_text(encoding="utf-8")
        assert "storage" not in codigo

    for nombre in ("asignaciones.py", "estudiantes.py"):
        codigo = (RAIZ_APP / "routes" / nombre).read_text(encoding="utf-8")
        assert "storage" not in codigo


def test_la_ruta_mis_clases_conserva_su_sql_inline():
    """Hallazgo de 6.0: hay SQL de dominio en la capa de rutas, no solo en el
    controlador. Ningun dominio migrado antes tenia esto, y 6.1 debera decidir
    que hacer con el. Se fija para que la extraccion no lo pierda de vista."""
    codigo = (RAIZ_APP / "routes" / "asignaciones.py").read_text(encoding="utf-8")
    sentencias = [
        nodo.value
        for nodo in ast.walk(ast.parse(codigo))
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and "SELECT" in nodo.value
    ]

    assert len(sentencias) == 1
    assert "FROM asignaciones a" in sentencias[0]
    assert "LEFT JOIN asignaciones base" in sentencias[0]
