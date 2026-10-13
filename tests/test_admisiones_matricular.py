"""Entrevista de admisión, paso E3: matricular desde una admisión aprobada.

Ver docs/funcionalidades/ENTREVISTA_ADMISION.md. Se prueban juntos
`admisiones_controller` y la matrícula del año en preparación de
`anios_lectivos_controller`, con dobles de los repositorios: no se escribe en
ningún tenant real.
"""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from psycopg2 import IntegrityError

from app.controllers import admisiones_controller as controlador
from app.controllers import anios_lectivos_controller as controlador_anios
from app.repositories import admisiones_repository as repositorio
from app.repositories import anios_lectivos_repository as repositorio_anios
from app.schemas.estudiante import EstudianteCreate


def _fila(**cambios):
    fila = {columna: None for columna in repositorio.COLUMNAS_DETALLE}
    fila.update(
        id=7,
        anio_lectivo_id=3,
        nombre="Lina",
        apellido="Díaz",
        documento_identidad="2001",
        curso_id=20,
        autoriza_datos=True,
        autoriza_nombre="Marta Díaz",
        resultado="aprobado",
        anio=2027,
        estado_anio="preparacion",
    )
    fila.update(cambios)
    return fila


def _ficha(**cambios):
    datos = {
        "nombre": "Lina",
        "apellido": "Díaz",
        "documento_identidad": "2001",
        "curso_id": 20,
        "direccion": "Calle 1",
        "colegio_anterior": "Lo que traiga la ficha",
        "estado": "retirado",
    }
    datos.update(cambios)
    return EstudianteCreate(**datos)


def _existente(**cambios):
    datos = {
        "id": 40,
        "nombre": "Lina",
        "apellido": "Díaz",
        "estado": "retirado",
        "curso_activo_id": None,
        "estado_salida": None,
        "matricula_destino_id": None,
    }
    datos.update(cambios)
    return datos


class ErrorDeIndice(IntegrityError):
    def __init__(self, regla):
        super().__init__(f"violates constraint \"{regla}\"")
        self._regla = regla

    @property
    def diag(self):
        return SimpleNamespace(constraint_name=self._regla)


@pytest.fixture
def entorno(monkeypatch):
    estado = SimpleNamespace(
        activo=(2, 2026, "activo"),
        destino=(3, 2027, "preparacion"),
        admision=_fila(),
        cursos={
            10: {"id": 10, "anio_lectivo_id": 2},
            20: {"id": 20, "anio_lectivo_id": 3},
        },
        existente=None,
        fallar=None,
        filas_copiadas=1,
        filas_enlazadas=1,
        eventos=[],
        commits=0,
        rollbacks=0,
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

    def registrar(nombre, resultado):
        def doble(*args, **_kwargs):
            estado.eventos.append((nombre, *args[1:]))
            if estado.fallar and estado.fallar[0] == nombre:
                raise estado.fallar[1]
            return resultado(*args[1:]) if callable(resultado) else resultado

        return doble

    def leer_admision(_cursor, admision_id, bloquear=False):
        estado.eventos.append(("leer", admision_id, bloquear))
        return dict(estado.admision) if admision_id == 7 else None

    def enlazar(admision_id, estudiante_id):
        estado.admision["estudiante_id"] = estudiante_id
        return estado.filas_enlazadas

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    monkeypatch.setattr(repositorio, "leer_admision", leer_admision)
    monkeypatch.setattr(
        repositorio, "buscar_estudiante_con_documento", registrar("aviso", None)
    )
    monkeypatch.setattr(
        repositorio,
        "copiar_datos_a_estudiante",
        registrar("copiar", lambda *_: estado.filas_copiadas),
    )
    monkeypatch.setattr(repositorio, "enlazar_estudiante", registrar("enlazar", enlazar))
    monkeypatch.setattr(
        repositorio_anios,
        "leer_anio_activo_para_actualizar",
        registrar("activo", lambda *_: estado.activo),
    )
    monkeypatch.setattr(
        repositorio_anios,
        "leer_anio_lectivo_para_actualizar",
        registrar("destino", lambda anio_id: estado.destino if anio_id == 3 else None),
    )
    monkeypatch.setattr(
        repositorio_anios,
        "leer_curso_para_matricula",
        registrar("curso", lambda curso_id: estado.cursos.get(curso_id)),
    )
    monkeypatch.setattr(
        repositorio_anios,
        "leer_estudiante_para_reingreso",
        registrar("reingreso", lambda *_: estado.existente),
        raising=False,
    )
    monkeypatch.setattr(
        repositorio_anios,
        "insertar_matricula_en_anio",
        registrar("matricula", lambda estudiante_id, *_: 1000 + estudiante_id),
    )
    monkeypatch.setattr(repositorio_anios, "sincronizar_curso_vigente", registrar("sincroniza", None))
    monkeypatch.setattr(
        controlador_anios.estudiantes_repository,
        "insertar_estudiante",
        registrar("crear_estudiante", 55),
    )
    monkeypatch.setattr(
        controlador_anios.estudiantes_repository,
        "actualizar_estudiante",
        registrar("actualizar_estudiante", lambda valores: (valores[-1],)),
    )
    return estado


def _nombres(estado):
    return [evento[0] for evento in estado.eventos]


def _evento(estado, nombre):
    return next(evento for evento in estado.eventos if evento[0] == nombre)


ESCRITURAS = ("crear_estudiante", "actualizar_estudiante", "matricula", "copiar", "enlazar")


def _sin_escrituras(estado):
    return not any(nombre in ESCRITURAS for nombre in _nombres(estado))


# ---------------------------------------------------------------------------
# Un aspirante nuevo
# ---------------------------------------------------------------------------


def test_matricula_un_aspirante_nuevo_en_una_sola_transaccion(entorno):
    respuesta = controlador.matricular_admision_controller(7, _ficha())

    nombres = _nombres(entorno)
    assert ("leer", 7, True) in entorno.eventos
    assert nombres.index("crear_estudiante") < nombres.index("matricula")
    assert nombres.index("matricula") < nombres.index("copiar")
    assert nombres.index("copiar") < nombres.index("enlazar")
    assert ("matricula", 55, 20, 3) in entorno.eventos
    assert ("copiar", 7, 55) in entorno.eventos
    assert ("enlazar", 7, 55) in entorno.eventos
    assert entorno.commits == 1
    assert respuesta["estudiante_id"] == 55
    assert respuesta["matricula_id"] == 1055
    assert respuesta["anio_lectivo_id"] == 3
    assert respuesta["curso_id"] == 20
    assert respuesta["estudiante_existente"] is False
    assert respuesta["mensaje"] == "Matrícula creada en 2027 para Lina Díaz."
    assert respuesta["admision"]["matriculada"] is True
    assert respuesta["admision"]["editable"] is False


def test_queda_activo_aunque_la_ficha_diga_otro_estado(entorno):
    controlador.matricular_admision_controller(7, _ficha(estado="retirado"))

    valores = _evento(entorno, "crear_estudiante")[1]
    assert len(valores) == 34
    assert valores[-1] == "activo"


def test_sin_documento_en_la_ficha_no_busca_un_estudiante_existente(entorno):
    controlador.matricular_admision_controller(7, _ficha(documento_identidad=None))

    assert "reingreso" not in _nombres(entorno)
    assert "crear_estudiante" in _nombres(entorno)


def test_busca_el_existente_por_el_documento_de_la_ficha_con_los_dos_anios(entorno):
    controlador.matricular_admision_controller(7, _ficha(documento_identidad="9009"))

    assert ("reingreso", "9009", 2, 3) in entorno.eventos


# ---------------------------------------------------------------------------
# Un exalumno que vuelve (decisión 11)
# ---------------------------------------------------------------------------


def test_un_exalumno_usa_su_mismo_registro_y_queda_activo(entorno):
    entorno.existente = _existente()

    respuesta = controlador.matricular_admision_controller(7, _ficha())

    assert "crear_estudiante" not in _nombres(entorno)
    valores = _evento(entorno, "actualizar_estudiante")[1]
    assert len(valores) == 35
    assert valores[-1] == 40
    assert valores[-2] == "activo"
    assert ("matricula", 40, 20, 3) in entorno.eventos
    assert ("copiar", 7, 40) in entorno.eventos
    assert ("enlazar", 7, 40) in entorno.eventos
    assert respuesta["estudiante_id"] == 40
    assert respuesta["estudiante_existente"] is True
    assert entorno.commits == 1


def test_un_retirado_durante_el_anio_activo_tambien_puede_volver(entorno):
    entorno.existente = _existente(curso_activo_id=10)

    respuesta = controlador.matricular_admision_controller(7, _ficha())

    assert respuesta["estudiante_existente"] is True


def test_quien_estudia_hoy_pasa_por_la_promocion(entorno):
    entorno.existente = _existente(estado="activo", curso_activo_id=10)

    with pytest.raises(controlador_anios.EstudianteNoReingresableError) as exc:
        controlador.matricular_admision_controller(7, _ficha())

    assert str(exc.value) == (
        "Lina Díaz estudia en 2026: pásalo a 2027 desde la promoción "
        "(Matricular estudiantes)."
    )
    assert _sin_escrituras(entorno)
    assert entorno.rollbacks == 1


def test_quien_ya_tiene_matricula_en_el_anio_no_se_matricula_otra_vez(entorno):
    entorno.existente = _existente(matricula_destino_id=900)

    with pytest.raises(controlador_anios.EstudianteNoReingresableError) as exc:
        controlador.matricular_admision_controller(7, _ficha())

    assert str(exc.value) == "Lina Díaz ya tiene matrícula en 2027."
    assert _sin_escrituras(entorno)


def test_quien_esta_marcado_como_que_no_sigue_necesita_quitar_la_marca(entorno):
    entorno.existente = _existente(curso_activo_id=10, estado_salida="retirado")

    with pytest.raises(controlador_anios.EstudianteNoReingresableError) as exc:
        controlador.matricular_admision_controller(7, _ficha())

    assert "Quita la marca" in str(exc.value)
    assert _sin_escrituras(entorno)


# ---------------------------------------------------------------------------
# Lo que no se matricula
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("resultado", ["pendiente", "no_aprobado"])
def test_solo_se_matricula_un_aprobado(entorno, resultado):
    entorno.admision = _fila(resultado=resultado)

    with pytest.raises(controlador.AdmisionNoAprobadaError) as exc:
        controlador.matricular_admision_controller(7, _ficha())

    assert str(exc.value) == "Solo se puede matricular a un aspirante aprobado."
    assert _sin_escrituras(entorno)


def test_no_se_matricula_dos_veces(entorno):
    entorno.admision = _fila(estudiante_id=55)

    with pytest.raises(controlador.AdmisionMatriculadaError):
        controlador.matricular_admision_controller(7, _ficha())

    assert _sin_escrituras(entorno)


def test_matricular_una_admision_que_no_existe(entorno):
    with pytest.raises(controlador.AdmisionNoEncontradaError):
        controlador.matricular_admision_controller(404, _ficha())


def test_no_se_matricula_si_el_anio_ya_no_esta_en_preparacion(entorno):
    entorno.destino = (3, 2027, "activo")

    with pytest.raises(controlador_anios.AnioLectivoDestinoInvalidoError):
        controlador.matricular_admision_controller(7, _ficha())

    assert _sin_escrituras(entorno)


def test_el_curso_de_la_ficha_es_del_anio_de_la_admision(entorno):
    with pytest.raises(controlador_anios.CursoMatriculaInvalidoError):
        controlador.matricular_admision_controller(7, _ficha(curso_id=10))

    assert _sin_escrituras(entorno)


# ---------------------------------------------------------------------------
# Choques al guardar: mensaje claro y nada a medias
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "paso,regla,mensaje",
    [
        (
            "crear_estudiante",
            "estudiantes_documento_identidad_key",
            "Ya hay un estudiante con el documento 2001. Vuelve a intentarlo.",
        ),
        (
            "matricula",
            "idx_matriculas_estudiante_anio_unico",
            "El estudiante ya tiene matrícula en 2027.",
        ),
        (
            "enlazar",
            "admisiones_estudiante_id_key",
            "Este estudiante ya está enlazado a la admisión de otro año. Por ahora "
            "un estudiante solo puede enlazarse a una admisión.",
        ),
    ],
)
def test_un_choque_de_la_base_sale_con_su_mensaje_y_deshace_todo(
    entorno, paso, regla, mensaje
):
    entorno.fallar = (paso, ErrorDeIndice(regla))

    with pytest.raises(controlador.AdmisionMatriculaConflictoError) as exc:
        controlador.matricular_admision_controller(7, _ficha())

    assert str(exc.value) == mensaje
    assert entorno.commits == 0
    assert entorno.rollbacks == 1


def test_otro_error_de_la_base_no_se_disfraza(entorno):
    entorno.fallar = ("matricula", ErrorDeIndice("otra_regla"))

    with pytest.raises(IntegrityError):
        controlador.matricular_admision_controller(7, _ficha())

    assert entorno.rollbacks == 1


@pytest.mark.parametrize("copiadas,enlazadas", [(0, 1), (1, 0)])
def test_si_no_se_copia_o_no_se_enlaza_se_deshace_todo(entorno, copiadas, enlazadas):
    entorno.filas_copiadas = copiadas
    entorno.filas_enlazadas = enlazadas

    with pytest.raises(controlador.AdmisionMatriculaConflictoError) as exc:
        controlador.matricular_admision_controller(7, _ficha())

    assert "Nada cambió" in str(exc.value)
    assert entorno.commits == 0
    assert entorno.rollbacks == 1


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------


class CursorFalso:
    def __init__(self, una=(), rowcount=1):
        self.una = list(una)
        self.rowcount = rowcount
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.una.pop(0) if self.una else None


def test_los_datos_que_se_copian_son_los_que_pasaron_a_la_entrevista():
    assert repositorio.COLUMNAS_COPIADAS_A_ESTUDIANTE == (
        "colegio_anterior",
        "anio_cursado_anterior",
        "pre_escolar_anterior",
        "ebp_anterior",
        "motivo_retiro_anterior",
        "paz_salvo_anterior",
        "ocupacion_padre",
        "ocupacion_madre",
    )


def test_copiar_no_borra_lo_que_el_estudiante_ya_tenia_si_la_entrevista_lo_dejo_vacio():
    cursor = CursorFalso(rowcount=1)

    filas = repositorio.copiar_datos_a_estudiante(cursor, 7, 55)

    sql, params = cursor.consultas[0]
    assert filas == 1
    assert sql.startswith("UPDATE estudiantes e SET ")
    for columna in repositorio.COLUMNAS_COPIADAS_A_ESTUDIANTE:
        assert f"{columna} = COALESCE(a.{columna}, e.{columna})" in sql
    assert sql.endswith("FROM admisiones a WHERE a.id = %s AND e.id = %s")
    assert params == (7, 55)


def test_enlazar_solo_un_aprobado_sin_estudiante():
    cursor = CursorFalso(rowcount=1)

    filas = repositorio.enlazar_estudiante(cursor, 7, 55)

    sql, params = cursor.consultas[0]
    assert filas == 1
    assert sql == (
        "UPDATE admisiones SET estudiante_id = %s, actualizado_en = CURRENT_TIMESTAMP "
        "WHERE id = %s AND estudiante_id IS NULL AND resultado = 'aprobado'"
    )
    assert params == (55, 7)


def test_el_estudiante_existente_se_lee_bloqueado_con_sus_matriculas_de_los_dos_anios():
    cursor = CursorFalso(una=[(40, "Lina", "Díaz", "retirado", 10, None, None)])

    existente = repositorio_anios.leer_estudiante_para_reingreso(cursor, "2001", 2, 3)

    sql, params = cursor.consultas[0]
    assert "FROM estudiantes e" in sql
    assert (
        "LEFT JOIN matriculas activa ON activa.estudiante_id = e.id "
        "AND activa.anio_lectivo_id = %s"
    ) in sql
    assert (
        "LEFT JOIN matriculas destino ON destino.estudiante_id = e.id "
        "AND destino.anio_lectivo_id = %s"
    ) in sql
    assert "WHERE e.documento_identidad = %s" in sql
    assert sql.endswith("FOR UPDATE OF e")
    assert params == (2, 3, "2001")
    assert existente == _existente(curso_activo_id=10)


def test_sin_estudiante_con_ese_documento_devuelve_none():
    assert repositorio_anios.leer_estudiante_para_reingreso(CursorFalso(), "1", 2, 3) is None
