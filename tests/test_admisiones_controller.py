"""Entrevista de admisión, paso E2: reglas y SQL de las admisiones.

Ver docs/funcionalidades/ENTREVISTA_ADMISION.md. Las pruebas usan dobles de
base de datos: no escriben en un tenant real.
"""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from psycopg2 import IntegrityError

from app.controllers import admisiones_controller as controlador
from app.repositories import admisiones_repository as repositorio
from app.schemas.admision import AdmisionCreate, AdmisionUpdate
from app.services.anio_lectivo import AnioLectivoInexistenteError


def _aspirante(**cambios):
    datos = {
        "nombre": "Lina",
        "apellido": "Díaz",
        "documento_identidad": "2001",
        "curso_id": 20,
        "autoriza_datos": True,
        "autoriza_nombre": "Marta Díaz",
    }
    datos.update(cambios)
    return datos


def _fila(admision_id=7, **cambios):
    """Una admisión como la devuelve `leer_admision`."""
    fila = {columna: None for columna in repositorio.COLUMNAS_DETALLE}
    fila.update(
        id=admision_id,
        anio_lectivo_id=3,
        nombre="Lina",
        apellido="Díaz",
        documento_identidad="2001",
        curso_id=20,
        autoriza_datos=True,
        autoriza_nombre="Marta Díaz",
        resultado="pendiente",
        anio=2027,
        estado_anio="preparacion",
        curso_nombre="PRIMERO A",
        curso_jornada="Mañana",
    )
    fila.update(cambios)
    return fila


class ErrorDeIndice(IntegrityError):
    """Un IntegrityError con el nombre de la regla, como lo da psycopg2."""

    def __init__(self, regla):
        super().__init__(f"duplicate key value violates unique constraint \"{regla}\"")
        self._regla = regla

    @property
    def diag(self):
        return SimpleNamespace(constraint_name=self._regla)


@pytest.fixture
def entorno(monkeypatch):
    estado = SimpleNamespace(
        anios={
            1: (1, 2025, "cerrado"),
            2: (2, 2026, "activo"),
            3: (3, 2027, "preparacion"),
        },
        cursos={
            10: {"id": 10, "anio_lectivo_id": 2},
            20: {"id": 20, "anio_lectivo_id": 3},
        },
        admisiones={7: _fila(7)},
        documentos_en_admisiones={},
        estudiantes_por_documento={},
        conteos={"pendiente": 1, "aprobado": 0, "no_aprobado": 0, "matriculado": 0, "total": 1},
        lista=[
            {"id": 7, "nombre": "Lina", "estudiante_id": None},
            {"id": 8, "nombre": "Juan", "estudiante_id": 55},
        ],
        error_al_guardar=None,
        filas_afectadas=1,
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

    def exigir_anio(cursor_recibido, anio_lectivo_id):
        assert cursor_recibido is cursor
        if anio_lectivo_id not in estado.anios:
            raise AnioLectivoInexistenteError("El año lectivo seleccionado no existe.")
        return estado.anios[anio_lectivo_id]

    def leer_curso(cursor_recibido, curso_id):
        estado.eventos.append(("curso", curso_id))
        return estado.cursos.get(curso_id)

    def leer_admision(cursor_recibido, admision_id, bloquear=False):
        estado.eventos.append(("leer", admision_id, bloquear))
        return estado.admisiones.get(admision_id)

    def insertar(cursor_recibido, anio_lectivo_id, valores):
        estado.eventos.append(("insertar", anio_lectivo_id, valores))
        if estado.error_al_guardar is not None:
            raise estado.error_al_guardar
        estado.admisiones[99] = _fila(99, anio_lectivo_id=anio_lectivo_id, **valores)
        return 99

    def actualizar(cursor_recibido, admision_id, valores):
        estado.eventos.append(("actualizar", admision_id, valores))
        if estado.error_al_guardar is not None:
            raise estado.error_al_guardar
        estado.admisiones[admision_id].update(valores)
        return estado.filas_afectadas

    def borrar(cursor_recibido, admision_id):
        estado.eventos.append(("borrar", admision_id))
        return estado.filas_afectadas

    def listar(cursor_recibido, anio_lectivo_id, resultado=None):
        estado.eventos.append(("listar", anio_lectivo_id, resultado))
        return estado.lista

    def contar(cursor_recibido, anio_lectivo_id):
        estado.eventos.append(("contar", anio_lectivo_id))
        return estado.conteos

    def buscar_admision(cursor_recibido, anio_lectivo_id, documento, excluir_id=None):
        estado.eventos.append(("documento_admision", anio_lectivo_id, documento, excluir_id))
        return estado.documentos_en_admisiones.get((anio_lectivo_id, documento))

    def buscar_estudiante(cursor_recibido, documento, excluir_id=None):
        estado.eventos.append(("documento_estudiante", documento, excluir_id))
        return estado.estudiantes_por_documento.get(documento)

    def guardar_resultado(cursor_recibido, admision_id, resultado, motivo):
        estado.eventos.append(("resultado", admision_id, resultado, motivo))
        estado.admisiones[admision_id].update(
            resultado=resultado, motivo_resultado=motivo
        )
        return estado.filas_afectadas

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    monkeypatch.setattr(controlador, "exigir_anio_lectivo", exigir_anio)
    monkeypatch.setattr(
        controlador.anios_lectivos_repository, "leer_curso_para_matricula", leer_curso
    )
    dobles = {
        "leer_admision": leer_admision,
        "insertar_admision": insertar,
        "actualizar_admision": actualizar,
        "borrar_admision": borrar,
        "listar_admisiones": listar,
        "contar_admisiones": contar,
        "buscar_admision_con_documento": buscar_admision,
        "buscar_estudiante_con_documento": buscar_estudiante,
        "guardar_resultado": guardar_resultado,
    }
    for nombre, doble in dobles.items():
        monkeypatch.setattr(controlador.admisiones_repository, nombre, doble)
    return estado


def _hubo(estado, tipo):
    return [evento for evento in estado.eventos if evento[0] == tipo]


# ---------------------------------------------------------------------------
# Listar
# ---------------------------------------------------------------------------


def test_lista_las_admisiones_del_anio_con_conteos_y_sin_escribir(entorno):
    respuesta = controlador.listar_admisiones_controller(3)

    assert respuesta["anio_lectivo"] == {"id": 3, "anio": 2027, "estado": "preparacion"}
    assert respuesta["editable"] is True
    assert respuesta["conteos"] == entorno.conteos
    assert [a["matriculada"] for a in respuesta["admisiones"]] == [False, True]
    assert ("abre", False) in entorno.eventos
    assert ("cierra",) in entorno.eventos


def test_el_filtro_de_resultado_llega_al_repositorio_y_los_conteos_son_del_anio(entorno):
    controlador.listar_admisiones_controller(3, "aprobado")

    assert ("listar", 3, "aprobado") in entorno.eventos
    assert ("contar", 3) in entorno.eventos


def test_un_anio_que_ya_no_esta_en_preparacion_se_consulta_pero_no_se_edita(entorno):
    respuesta = controlador.listar_admisiones_controller(1)

    assert respuesta["anio_lectivo"]["estado"] == "cerrado"
    assert respuesta["editable"] is False


def test_listar_un_anio_que_no_existe(entorno):
    with pytest.raises(AnioLectivoInexistenteError):
        controlador.listar_admisiones_controller(404)


# ---------------------------------------------------------------------------
# Registrar
# ---------------------------------------------------------------------------


def test_registra_el_aspirante_pendiente_en_el_anio_en_preparacion(entorno):
    detalle = controlador.registrar_admision_controller(3, AdmisionCreate(**_aspirante()))

    [insercion] = _hubo(entorno, "insertar")
    assert insercion[1] == 3
    assert insercion[2]["nombre"] == "Lina"
    assert "resultado" not in insercion[2]
    assert detalle["id"] == 99
    assert detalle["resultado"] == "pendiente"
    assert detalle["matriculada"] is False
    assert detalle["editable"] is True
    assert detalle["aviso_documento"] is None
    assert entorno.commits == 1


@pytest.mark.parametrize("anio_id,anio", [(2, 2026), (1, 2025)])
def test_no_registra_en_un_anio_que_no_esta_en_preparacion(entorno, anio_id, anio):
    with pytest.raises(controlador.AnioNoEnPreparacionError) as exc:
        controlador.registrar_admision_controller(
            anio_id, AdmisionCreate(**_aspirante(curso_id=None))
        )

    assert str(anio) in str(exc.value)
    assert not _hubo(entorno, "insertar")
    assert entorno.rollbacks == 1
    assert entorno.eventos[-1] == ("cierra",)


def test_registrar_en_un_anio_que_no_existe(entorno):
    with pytest.raises(AnioLectivoInexistenteError):
        controlador.registrar_admision_controller(404, AdmisionCreate(**_aspirante()))


@pytest.mark.parametrize("curso_id", [10, 999])
def test_el_curso_tiene_que_ser_un_curso_activo_del_mismo_anio(entorno, curso_id):
    with pytest.raises(controlador.CursoAdmisionInvalidoError) as exc:
        controlador.registrar_admision_controller(
            3, AdmisionCreate(**_aspirante(curso_id=curso_id))
        )

    assert "2027" in str(exc.value)
    assert not _hubo(entorno, "insertar")


def test_sin_curso_no_consulta_cursos(entorno):
    controlador.registrar_admision_controller(3, AdmisionCreate(**_aspirante(curso_id=None)))

    assert not _hubo(entorno, "curso")


def test_no_repite_documento_en_el_mismo_anio(entorno):
    entorno.documentos_en_admisiones[(3, "2001")] = 7

    with pytest.raises(controlador.DocumentoAdmisionRepetidoError) as exc:
        controlador.registrar_admision_controller(3, AdmisionCreate(**_aspirante()))

    assert str(exc.value) == "Ya hay un aspirante con el documento 2001 en 2027."
    assert not _hubo(entorno, "insertar")


def test_sin_documento_no_busca_repetidos(entorno):
    controlador.registrar_admision_controller(
        3, AdmisionCreate(**_aspirante(documento_identidad=None))
    )

    assert not _hubo(entorno, "documento_admision")
    assert not _hubo(entorno, "documento_estudiante")


def test_dos_altas_a_la_vez_con_el_mismo_documento_dan_el_mismo_mensaje(entorno):
    entorno.error_al_guardar = ErrorDeIndice("idx_admisiones_documento_por_anio")

    with pytest.raises(controlador.DocumentoAdmisionRepetidoError) as exc:
        controlador.registrar_admision_controller(3, AdmisionCreate(**_aspirante()))

    # El mensaje es el escrito aquí, nunca el texto de PostgreSQL.
    assert str(exc.value) == "Ya hay un aspirante con el documento 2001 en 2027."
    assert entorno.rollbacks == 1


def test_otro_error_de_la_base_no_se_disfraza(entorno):
    entorno.error_al_guardar = ErrorDeIndice("otra_regla")

    with pytest.raises(IntegrityError):
        controlador.registrar_admision_controller(3, AdmisionCreate(**_aspirante()))

    assert entorno.rollbacks == 1


def test_avisa_si_el_documento_ya_es_de_un_estudiante_pero_registra(entorno):
    entorno.estudiantes_por_documento["2001"] = {
        "id": 55,
        "nombre": "Lina",
        "apellido": "Díaz",
        "estado": "retirado",
    }

    detalle = controlador.registrar_admision_controller(3, AdmisionCreate(**_aspirante()))

    aviso = detalle["aviso_documento"]
    assert aviso["estudiante_id"] == 55
    assert aviso["estado"] == "retirado"
    assert aviso["mensaje"] == (
        "El documento 2001 ya es de un estudiante del colegio: Lina Díaz "
        "(retirado). Al matricular, chocaría con ese estudiante."
    )
    assert entorno.commits == 1


# ---------------------------------------------------------------------------
# Ver
# ---------------------------------------------------------------------------


def test_ver_una_admision(entorno):
    detalle = controlador.obtener_admision_controller(7)

    assert detalle["id"] == 7
    assert detalle["curso_nombre"] == "PRIMERO A"
    assert detalle["editable"] is True
    assert ("leer", 7, False) in entorno.eventos
    assert ("abre", False) in entorno.eventos


def test_ver_una_admision_que_no_existe(entorno):
    with pytest.raises(controlador.AdmisionNoEncontradaError) as exc:
        controlador.obtener_admision_controller(404)

    assert str(exc.value) == "La admisión no existe."


def test_una_matriculada_no_se_avisa_a_si_misma_ni_es_editable(entorno):
    entorno.admisiones[7] = _fila(7, resultado="aprobado", estudiante_id=55)

    detalle = controlador.obtener_admision_controller(7)

    assert detalle["matriculada"] is True
    assert detalle["editable"] is False
    assert ("documento_estudiante", "2001", 55) in entorno.eventos


def test_una_de_un_anio_que_ya_no_esta_en_preparacion_no_es_editable(entorno):
    entorno.admisiones[7] = _fila(7, anio=2026, estado_anio="activo")

    assert controlador.obtener_admision_controller(7)["editable"] is False


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------


def test_edita_los_datos_y_la_entrevista_con_la_fila_bloqueada(entorno):
    datos = AdmisionUpdate(
        **_aspirante(entrevistador="Psicóloga Ruiz", observaciones="Familia puntual")
    )

    detalle = controlador.actualizar_admision_controller(7, datos)

    assert ("leer", 7, True) in entorno.eventos
    [actualizacion] = _hubo(entorno, "actualizar")
    assert actualizacion[2]["entrevistador"] == "Psicóloga Ruiz"
    assert "resultado" not in actualizacion[2]
    assert detalle["observaciones"] == "Familia puntual"
    assert entorno.commits == 1


def test_al_editar_el_documento_no_choca_consigo_mismo(entorno):
    controlador.actualizar_admision_controller(7, AdmisionUpdate(**_aspirante()))

    assert ("documento_admision", 3, "2001", 7) in entorno.eventos


def test_al_editar_el_curso_se_valida_con_el_anio_de_la_admision(entorno):
    with pytest.raises(controlador.CursoAdmisionInvalidoError):
        controlador.actualizar_admision_controller(
            7, AdmisionUpdate(**_aspirante(curso_id=10))
        )

    assert not _hubo(entorno, "actualizar")


def test_no_edita_una_matriculada(entorno):
    entorno.admisiones[7] = _fila(7, resultado="aprobado", estudiante_id=55)

    with pytest.raises(controlador.AdmisionMatriculadaError) as exc:
        controlador.actualizar_admision_controller(7, AdmisionUpdate(**_aspirante()))

    assert str(exc.value) == "Esta admisión ya está matriculada. Solo se puede consultar."
    assert not _hubo(entorno, "actualizar")
    assert entorno.rollbacks == 1


def test_no_edita_una_de_un_anio_que_ya_no_esta_en_preparacion(entorno):
    entorno.admisiones[7] = _fila(7, anio=2026, estado_anio="activo")

    with pytest.raises(controlador.AnioNoEnPreparacionError) as exc:
        controlador.actualizar_admision_controller(7, AdmisionUpdate(**_aspirante()))

    assert "2026" in str(exc.value)
    assert not _hubo(entorno, "actualizar")


def test_editar_una_admision_que_no_existe(entorno):
    with pytest.raises(controlador.AdmisionNoEncontradaError):
        controlador.actualizar_admision_controller(404, AdmisionUpdate(**_aspirante()))


def test_editar_con_un_documento_que_ya_tiene_otro_aspirante(entorno):
    entorno.documentos_en_admisiones[(3, "3003")] = 8

    with pytest.raises(controlador.DocumentoAdmisionRepetidoError):
        controlador.actualizar_admision_controller(
            7, AdmisionUpdate(**_aspirante(documento_identidad="3003"))
        )

    assert not _hubo(entorno, "actualizar")


def test_si_se_matriculo_mientras_tanto_no_se_pisa(entorno):
    entorno.filas_afectadas = 0

    with pytest.raises(controlador.AdmisionMatriculadaError):
        controlador.actualizar_admision_controller(7, AdmisionUpdate(**_aspirante()))

    assert entorno.rollbacks == 1


# ---------------------------------------------------------------------------
# Borrar
# ---------------------------------------------------------------------------


def test_borra_una_admision_no_matriculada(entorno):
    respuesta = controlador.borrar_admision_controller(7)

    assert respuesta == {"mensaje": "Admisión borrada", "id": 7}
    assert ("leer", 7, True) in entorno.eventos
    assert ("borrar", 7) in entorno.eventos
    assert entorno.commits == 1


def test_no_borra_una_matriculada(entorno):
    entorno.admisiones[7] = _fila(7, resultado="aprobado", estudiante_id=55)

    with pytest.raises(controlador.AdmisionMatriculadaError):
        controlador.borrar_admision_controller(7)

    assert not _hubo(entorno, "borrar")


def test_no_borra_una_de_un_anio_que_ya_no_esta_en_preparacion(entorno):
    entorno.admisiones[7] = _fila(7, anio=2026, estado_anio="activo")

    with pytest.raises(controlador.AnioNoEnPreparacionError):
        controlador.borrar_admision_controller(7)

    assert not _hubo(entorno, "borrar")


def test_borrar_una_admision_que_no_existe(entorno):
    with pytest.raises(controlador.AdmisionNoEncontradaError):
        controlador.borrar_admision_controller(404)


def test_si_se_matriculo_mientras_tanto_no_se_borra(entorno):
    entorno.filas_afectadas = 0

    with pytest.raises(controlador.AdmisionMatriculadaError):
        controlador.borrar_admision_controller(7)

    assert entorno.rollbacks == 1


# ---------------------------------------------------------------------------
# Resultado (paso E3)
# ---------------------------------------------------------------------------


def _resultado(**datos):
    from app.schemas.admision import ResultadoAdmisionUpdate

    return ResultadoAdmisionUpdate(**datos)


def test_aprobar_guarda_el_resultado_con_la_fila_bloqueada(entorno):
    detalle = controlador.cambiar_resultado_controller(7, _resultado(resultado="aprobado"))

    assert ("leer", 7, True) in entorno.eventos
    assert ("resultado", 7, "aprobado", None) in entorno.eventos
    assert detalle["resultado"] == "aprobado"
    assert entorno.commits == 1


def test_no_aprobar_guarda_el_motivo(entorno):
    controlador.cambiar_resultado_controller(
        7, _resultado(resultado="no_aprobado", motivo_resultado=" Cupo lleno ")
    )

    assert ("resultado", 7, "no_aprobado", "Cupo lleno") in entorno.eventos


def test_se_puede_volver_a_pendiente_mientras_no_este_matriculada(entorno):
    entorno.admisiones[7] = _fila(7, resultado="aprobado")

    detalle = controlador.cambiar_resultado_controller(7, _resultado(resultado="pendiente"))

    assert detalle["resultado"] == "pendiente"


def test_no_cambia_el_resultado_de_una_matriculada(entorno):
    entorno.admisiones[7] = _fila(7, resultado="aprobado", estudiante_id=55)

    with pytest.raises(controlador.AdmisionMatriculadaError):
        controlador.cambiar_resultado_controller(7, _resultado(resultado="pendiente"))

    assert not _hubo(entorno, "resultado")


def test_no_cambia_el_resultado_si_el_anio_ya_no_esta_en_preparacion(entorno):
    entorno.admisiones[7] = _fila(7, anio=2026, estado_anio="activo")

    with pytest.raises(controlador.AnioNoEnPreparacionError):
        controlador.cambiar_resultado_controller(7, _resultado(resultado="aprobado"))

    assert not _hubo(entorno, "resultado")


def test_resultado_de_una_admision_que_no_existe(entorno):
    with pytest.raises(controlador.AdmisionNoEncontradaError):
        controlador.cambiar_resultado_controller(404, _resultado(resultado="aprobado"))


def test_si_se_matriculo_mientras_tanto_no_cambia_el_resultado(entorno):
    entorno.filas_afectadas = 0

    with pytest.raises(controlador.AdmisionMatriculadaError):
        controlador.cambiar_resultado_controller(7, _resultado(resultado="pendiente"))

    assert entorno.rollbacks == 1


# ---------------------------------------------------------------------------
# SQL del repositorio
# ---------------------------------------------------------------------------


class CursorFalso:
    def __init__(self, una=(), todas=(), rowcount=1):
        self.una = list(una)
        self.todas = list(todas)
        self.rowcount = rowcount
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.una.pop(0) if self.una else None

    def fetchall(self):
        return self.todas.pop(0) if self.todas else []


def _valores_completos():
    valores = {columna: f"v_{columna}" for columna in repositorio.COLUMNAS_ASPIRANTE}
    valores.update({columna: f"v_{columna}" for columna in repositorio.COLUMNAS_ENTREVISTA})
    return valores


def test_insertar_guarda_solo_los_datos_del_aspirante_y_el_anio():
    cursor = CursorFalso(una=[(41,)])
    valores = _valores_completos()

    admision_id = repositorio.insertar_admision(cursor, 3, valores)

    sql, params = cursor.consultas[0]
    assert admision_id == 41
    assert sql.startswith("INSERT INTO admisiones (anio_lectivo_id, nombre, apellido,")
    assert sql.endswith("RETURNING id")
    assert params == (3, *[valores[c] for c in repositorio.COLUMNAS_ASPIRANTE])
    for ajena in ("resultado", "estudiante_id", "entrevistador", "observaciones"):
        assert ajena not in sql


def test_actualizar_no_toca_el_resultado_ni_una_matriculada():
    cursor = CursorFalso(rowcount=1)
    valores = _valores_completos()

    filas = repositorio.actualizar_admision(cursor, 7, valores)

    sql, params = cursor.consultas[0]
    assert filas == 1
    assert sql.startswith("UPDATE admisiones SET nombre = %s, apellido = %s,")
    assert "observaciones = %s" in sql
    assert "actualizado_en = CURRENT_TIMESTAMP" in sql
    assert sql.endswith("WHERE id = %s AND estudiante_id IS NULL")
    columnas = repositorio.COLUMNAS_ASPIRANTE + repositorio.COLUMNAS_ENTREVISTA
    assert params == (*[valores[c] for c in columnas], 7)
    for ajena in ("resultado", "motivo_resultado", "decidido_en", "anio_lectivo_id"):
        assert ajena not in sql


def test_borrar_solo_borra_una_no_matriculada():
    cursor = CursorFalso(rowcount=0)

    filas = repositorio.borrar_admision(cursor, 7)

    sql, params = cursor.consultas[0]
    assert filas == 0
    assert sql == "DELETE FROM admisiones WHERE id = %s AND estudiante_id IS NULL"
    assert params == (7,)


def test_leer_trae_la_admision_con_su_anio_y_su_curso():
    fila = tuple(f"v{i}" for i in range(len(repositorio.COLUMNAS_DETALLE)))
    cursor = CursorFalso(una=[fila])

    admision = repositorio.leer_admision(cursor, 7)

    sql, params = cursor.consultas[0]
    assert "JOIN anios_lectivos al ON al.id = a.anio_lectivo_id" in sql
    assert "LEFT JOIN cursos c ON c.id = a.curso_id" in sql
    assert "FOR UPDATE" not in sql
    assert params == (7,)
    assert list(admision) == list(repositorio.COLUMNAS_DETALLE)
    assert admision["estado_anio"] == fila[repositorio.COLUMNAS_DETALLE.index("estado_anio")]


def test_leer_para_editar_bloquea_solo_la_admision():
    cursor = CursorFalso()

    assert repositorio.leer_admision(cursor, 7, bloquear=True) is None

    sql, _params = cursor.consultas[0]
    assert sql.endswith("FOR UPDATE OF a")


def test_listar_es_del_anio_y_filtra_por_resultado_si_se_pide():
    fila = tuple(f"v{i}" for i in range(len(repositorio.COLUMNAS_LISTA)))
    cursor = CursorFalso(todas=[[fila], []])

    filas = repositorio.listar_admisiones(cursor, 3)
    repositorio.listar_admisiones(cursor, 3, "no_aprobado")

    sin_filtro, params_sin = cursor.consultas[0]
    con_filtro, params_con = cursor.consultas[1]
    assert "WHERE a.anio_lectivo_id = %s" in sin_filtro
    assert "a.resultado = %s" not in sin_filtro
    assert params_sin == (3,)
    assert "AND a.resultado = %s" in con_filtro
    assert params_con == (3, "no_aprobado")
    assert "ORDER BY a.apellido, a.nombre, a.id" in sin_filtro
    assert list(filas[0]) == list(repositorio.COLUMNAS_LISTA)


def test_contar_da_los_tres_resultados_las_matriculadas_y_el_total():
    cursor = CursorFalso(una=[(4, 2, 1, 1, 7)])

    conteos = repositorio.contar_admisiones(cursor, 3)

    sql, params = cursor.consultas[0]
    assert conteos == {
        "pendiente": 4,
        "aprobado": 2,
        "no_aprobado": 1,
        "matriculado": 1,
        "total": 7,
    }
    assert "COUNT(*) FILTER (WHERE resultado = 'pendiente')" in sql
    assert "COUNT(estudiante_id)" in sql
    assert params == (3,)


def test_buscar_documento_repetido_en_el_anio():
    cursor = CursorFalso(una=[(8,), None])

    assert repositorio.buscar_admision_con_documento(cursor, 3, "2001") == 8
    assert repositorio.buscar_admision_con_documento(cursor, 3, "2001", excluir_id=7) is None

    sql, params = cursor.consultas[0]
    assert "WHERE anio_lectivo_id = %s AND documento_identidad = %s" in sql
    assert "id <> %s" not in sql
    assert params == (3, "2001")
    sql_excluyendo, params_excluyendo = cursor.consultas[1]
    assert "AND id <> %s" in sql_excluyendo
    assert params_excluyendo == (3, "2001", 7)


def test_buscar_estudiante_con_el_mismo_documento():
    cursor = CursorFalso(una=[(55, "Lina", "Díaz", "retirado"), None])

    estudiante = repositorio.buscar_estudiante_con_documento(cursor, "2001")
    otro = repositorio.buscar_estudiante_con_documento(cursor, "2001", excluir_id=55)

    sql, params = cursor.consultas[0]
    assert "FROM estudiantes WHERE documento_identidad = %s" in sql
    assert params == ("2001",)
    assert estudiante == {"id": 55, "nombre": "Lina", "apellido": "Díaz", "estado": "retirado"}
    sql_excluyendo, params_excluyendo = cursor.consultas[1]
    assert "AND id <> %s" in sql_excluyendo
    assert params_excluyendo == ("2001", 55)
    assert otro is None


def test_guardar_resultado_marca_cuando_se_decidio_y_no_toca_una_matriculada():
    cursor = CursorFalso(rowcount=1)

    filas = repositorio.guardar_resultado(cursor, 7, "no_aprobado", "Cupo lleno")
    repositorio.guardar_resultado(cursor, 7, "pendiente", None)

    sql, params = cursor.consultas[0]
    assert filas == 1
    assert sql == (
        "UPDATE admisiones SET resultado = %s, motivo_resultado = %s, "
        "decidido_en = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END, "
        "actualizado_en = CURRENT_TIMESTAMP "
        "WHERE id = %s AND estudiante_id IS NULL"
    )
    assert params == ("no_aprobado", "Cupo lleno", True, 7)
    # Volver a pendiente borra la fecha de la decisión.
    assert cursor.consultas[1][1] == ("pendiente", None, False, 7)
