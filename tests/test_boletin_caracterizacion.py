"""Caracterizacion de la subcapa 7.0 del dominio `boletin`.

Fija el comportamiento observable ANTES de cualquier extraccion: frontera del
dominio, entradas HTTP, permisos, status codes, semantica transaccional, las
cifras y la linea base de consultas y de conexiones.

No corrige ningun hallazgo. Varias pruebas son deliberadamente guardias de
linea base: si una extraccion posterior cambia el conteo de sentencias, el
idioma de conexion o el numero de archivos, deben fallar y obligar a una
decision explicita.
"""

import ast
import inspect
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.controllers import boletin_controller
from app.core import permissions
from app.core.nivel_academico import NOMBRE_MATERIA_ASISTENCIA_JORNADA
from app.routes import boletines, notas

RAIZ = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Dobles
# --------------------------------------------------------------------------

class CursorFalso:
    """Cursor que registra cada `execute` y sirve filas preprogramadas."""

    def __init__(self, una_fila=None, filas=None, secuencia_fetchone=None,
                 secuencia_fetchall=None):
        self.una_fila = una_fila
        self.filas = filas if filas is not None else []
        self.secuencia_fetchone = list(secuencia_fetchone or [])
        self.secuencia_fetchall = list(secuencia_fetchall or [])
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        if self.secuencia_fetchone:
            return self.secuencia_fetchone.pop(0)
        return self.una_fila

    def fetchall(self):
        if self.secuencia_fetchall:
            return self.secuencia_fetchall.pop(0)
        return self.filas

    def close(self):
        self.closed = True


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.closed = False
        self.commits = 0
        self.rollbacks = 0

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class ContadorDeConexiones:
    """Cuenta cuantas veces se pide una conexion, sin simultanearlas."""

    def __init__(self):
        self.abiertas = 0

    def __call__(self):
        self.abiertas += 1
        return ConexionFalsa(
            CursorFalso(
                una_fila={
                    "estudiante_nombre": "Sara",
                    "estudiante_apellido": "López",
                    "curso_nombre": "Quinto",
                },
                filas=[],
            )
        )


def _sql_del_modulo(ruta_relativa):
    """Literales SQL de un modulo, extraidos por AST y no por texto."""
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))
    literales = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        atributo = getattr(nodo.func, "attr", None)
        if atributo != "execute":
            continue
        if nodo.args and isinstance(nodo.args[0], ast.Constant):
            valor = nodo.args[0].value
            if isinstance(valor, str):
                literales.append(valor)
        elif nodo.args and isinstance(nodo.args[0], ast.JoinedStr):
            # Año lectivo, fase 3 (paso 3.5a): cinco consultas llevan un hueco
            # para el curso del estudiante (`e.curso_id` o el de su matricula
            # de un año). Siguen siendo una sentencia cada una; se cuentan con
            # su texto fijo y el hueco marcado.
            literales.append("".join(
                parte.value if isinstance(parte, ast.Constant) else "{...}"
                for parte in nodo.args[0].values
            ))
    return literales


def _paths_declarados(router):
    return {
        (ruta.path, tuple(sorted(ruta.methods)))
        for ruta in router.routes
        if hasattr(ruta, "methods")
    }


class _BoletinFalso:
    def __init__(self, estudiante_id=8, asignacion_id=44, periodo=2,
                 definitiva=4.5, detalles=()):
        self.estudiante_id = estudiante_id
        self.asignacion_id = asignacion_id
        self.periodo = periodo
        self.definitiva = definitiva
        self.tipo_evaluacion = "numerica"
        self.detalles = list(detalles)


class _DetalleFalso:
    def __init__(self, nota=4.0, observacion="ok", tipo_evaluacion="numerica",
                 valoracion=None):
        self.nota = nota
        self.observacion = observacion
        self.tipo_evaluacion = tipo_evaluacion
        self.valoracion = valoracion


# --------------------------------------------------------------------------
# Frontera del dominio
# --------------------------------------------------------------------------

def test_el_dominio_son_cuatro_archivos_y_sigue_sin_servicio():
    """Guardia de frontera, actualizada por 7.1.

    7.0 la dejo en tres archivos y sin repositorio. 7.1 anadio el decimo
    repositorio del proyecto; el servicio sigue sin existir y crearlo seria otra
    decision, no un efecto colateral.
    """
    assert (RAIZ / "app/routes/boletines.py").is_file()
    assert (RAIZ / "app/controllers/boletin_controller.py").is_file()
    assert (RAIZ / "app/schemas/boletin.py").is_file()
    assert (RAIZ / "app/repositories/boletin_repository.py").is_file()

    assert not (RAIZ / "app/services/boletin_service.py").exists()


def test_el_router_declara_exactamente_las_cuatro_entradas_del_dominio():
    assert _paths_declarados(boletines.router) == {
        ("/boletines/guardar", ("POST",)),
        ("/boletines/referencia/{asignacion_id}/{periodo}", ("GET",)),
        ("/boletines/admin/generar/{estudiante_id}/{periodo}", ("GET",)),
        ("/boletines/admin/reporte-parcial/{estudiante_id}/{periodo}", ("GET",)),
    }


def test_notas_conserva_las_dos_rutas_de_boletin_y_no_hay_colision_de_paths():
    """La frontera esta partida y NO coincide con los nombres de archivo.

    `notas` posee dos rutas de boletin desde antes de esta capa; su 7.1 ya
    cerro su persistencia. Esta prueba fija que siguen alli y que ningun path
    de `/boletines` colisiona con uno de `/boletin`.
    """
    paths_notas = {path for path, _ in _paths_declarados(notas.router)}
    assert "/boletin/{estudiante_id}" in paths_notas
    assert "/boletin/detallado/{estudiante_id}" in paths_notas

    paths_boletines = {path for path, _ in _paths_declarados(boletines.router)}
    assert paths_notas.isdisjoint(paths_boletines)
    assert all(path.startswith("/boletines/") for path in paths_boletines)


def test_la_persistencia_vive_en_el_repositorio_y_solo_queda_una_inline():
    """Linea base de SQL inline, actualizada por 7.1.

    7.0 conto **12 sentencias** en el controlador. 7.1 movio **11** al
    repositorio y dejo **1**: la del codigo muerto de `planilla`, que no
    pertenece a este dominio.
    """
    assert len(_sql_del_modulo("app/controllers/boletin_controller.py")) == 1
    assert len(_sql_del_modulo("app/repositories/boletin_repository.py")) == 11
    assert _sql_del_modulo("app/routes/boletines.py") == []


def test_el_conjunto_de_sql_del_dominio_sigue_siendo_el_mismo():
    """La extraccion movio texto, no lo cambio.

    Union de literales del controlador y del repositorio: 12, los mismos que
    7.0 inventario.
    """
    total = (
        _sql_del_modulo("app/controllers/boletin_controller.py")
        + _sql_del_modulo("app/repositories/boletin_repository.py")
    )
    assert len(total) == 12


def test_el_repositorio_no_es_dueno_de_ningun_recurso():
    """Ninguna funcion del repositorio abre, cierra, confirma ni revierte.

    La propiedad de la conexion sigue en el controlador, igual que en los nueve
    repositorios anteriores.
    """
    fuente = (RAIZ / "app/repositories/boletin_repository.py").read_text(encoding="utf-8")
    for prohibido in ("get_connection", "get_cursor", "commit()", "rollback()", "close()"):
        assert prohibido not in fuente


def test_el_controlador_usa_el_idioma_antiguo_get_connection():
    """La capa 1 no migro este archivo: sigue en `get_connection()` y no usa
    `get_cursor()`. Es un hecho de linea base, no un defecto que 7.0 corrija."""
    fuente = (RAIZ / "app/controllers/boletin_controller.py").read_text(encoding="utf-8")
    assert "get_connection" in fuente
    assert "get_cursor" not in fuente


def test_obtener_notas_planilla_controller_es_codigo_muerto_de_otro_dominio():
    """Hallazgo registrado y NO corregido: una funcion de `planilla` vive en el
    controlador de `boletin` y no la importa nadie."""
    assert hasattr(boletin_controller, "obtener_notas_planilla_controller")

    # Se buscan puntos de llamada reales, no menciones: las bitacoras y este
    # mismo archivo nombran la funcion sin invocarla.
    consumidores = []
    propios = {"boletin_controller.py", Path(__file__).name}
    for carpeta in ("app", "tests"):
        for archivo in (RAIZ / carpeta).rglob("*.py"):
            if archivo.name in propios:
                continue
            if "obtener_notas_planilla_controller(" in archivo.read_text(encoding="utf-8"):
                consumidores.append(archivo.name)

    assert consumidores == []


# --------------------------------------------------------------------------
# Escritura y semantica transaccional
# --------------------------------------------------------------------------

def test_guardar_boletin_escribe_dos_tablas_con_reemplazo_parcial(monkeypatch):
    cursor = CursorFalso(secuencia_fetchone=[(77,), (901,)])
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: None,
    )

    datos = _BoletinFalso(detalles=[_DetalleFalso(), _DetalleFalso(nota=3.0)])
    resultado = boletin_controller.guardar_boletin_controller(datos)

    assert resultado == {"mensaje": "Boletín guardado exitosamente"}

    sentencias = [sql for sql, _ in cursor.calls]
    assert len(sentencias) == 4
    assert "INSERT INTO boletin_cabecera" in sentencias[0]
    assert "ON CONFLICT (estudiante_id, asignacion_id, periodo)" in sentencias[0]
    assert sentencias[1] == "DELETE FROM boletin_detalles WHERE boletin_id = %s"
    assert "INSERT INTO boletin_detalles" in sentencias[2]
    assert "INSERT INTO boletin_detalles" in sentencias[3]

    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert cursor.closed is True
    assert conn.closed is True


def test_guardar_boletin_escribe_el_asignacion_academica_id_resuelto(monkeypatch):
    cursor = CursorFalso(secuencia_fetchone=[(77,)])
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: None,
    )

    boletin_controller.guardar_boletin_controller(_BoletinFalso(asignacion_id=44))

    _, params_cabecera = cursor.calls[0]
    assert params_cabecera == (8, 55, 2, 4.5)


def test_guardar_boletin_revierte_y_propaga_el_error(monkeypatch):
    class CursorQueFalla(CursorFalso):
        def execute(self, query, params=None):
            super().execute(query, params)
            raise RuntimeError("fallo de escritura")

    cursor = CursorQueFalla()
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: None,
    )

    with pytest.raises(RuntimeError):
        boletin_controller.guardar_boletin_controller(_BoletinFalso())

    assert conn.rollbacks == 1
    assert conn.commits == 0
    assert cursor.closed is True
    assert conn.closed is True


def test_guardar_boletin_en_curso_preescolar_fuerza_desarrollo_en_todos_los_detalles(
    monkeypatch,
):
    """El nivel del curso manda sobre lo que pida cada detalle del boletin.

    Antes de la funcionalidad de nivel academico, cada detalle podia llevar su
    propio tipo_evaluacion sin ninguna relacion con el curso real. Un curso
    preescolar guarda "desarrollo" en todos sus detalles, aunque el cliente
    pida "numerica" en alguno.
    """
    cursor = CursorFalso(secuencia_fetchone=[(77,)])
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: "preescolar",
    )

    detalles = [
        _DetalleFalso(tipo_evaluacion="numerica"),
        _DetalleFalso(tipo_evaluacion="desarrollo", valoracion="Alto"),
    ]
    boletin_controller.guardar_boletin_controller(_BoletinFalso(detalles=detalles))

    _, params_detalle1 = cursor.calls[2]
    _, params_detalle2 = cursor.calls[3]
    assert params_detalle1[3] == "desarrollo"
    assert params_detalle2[3] == "desarrollo"


def test_guardar_boletin_en_curso_primaria_fuerza_numerica_aunque_pidan_desarrollo(
    monkeypatch,
):
    """Primaria fuerza numerica, igual que preescolar fuerza desarrollo:
    ningun nivel definido es libre."""
    cursor = CursorFalso(secuencia_fetchone=[(77,)])
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: "primaria",
    )

    detalles = [_DetalleFalso(tipo_evaluacion="desarrollo", valoracion="Alto")]
    boletin_controller.guardar_boletin_controller(_BoletinFalso(detalles=detalles))

    _, params_detalle = cursor.calls[2]
    assert params_detalle[3] == "numerica"


def test_boletin_de_admin_excluye_la_asignacion_de_jornada(monkeypatch):
    """La asignacion de jornada (nivel academico, preescolar) no es una
    materia real: no debe aparecer en el boletin oficial del estudiante."""
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara", "estudiante_apellido": "López",
            "curso_nombre": "Transición A", "puesto": 1, "total": 20,
        },
        secuencia_fetchall=[[], []],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    boletin_controller.obtener_boletin_admin_controller(8, 2)

    _, params_materias = cursor.calls[0]
    assert params_materias[-1] == NOMBRE_MATERIA_ASISTENCIA_JORNADA


def test_reporte_parcial_excluye_la_asignacion_de_jornada(monkeypatch):
    """Mismo criterio que el boletin oficial, para el reporte parcial."""
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara", "estudiante_apellido": "López",
            "curso_nombre": "Transición A",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    _, params_planilla = cursor.calls[1]
    assert params_planilla[-1] == NOMBRE_MATERIA_ASISTENCIA_JORNADA


def test_las_dos_consultas_del_boletin_dejan_fuera_las_materias_inactivas():
    """Una asignatura inactiva no aparece en el boletin ni en el parcial.

    El filtro llego tarde: `materias.estado` se anadio en
    20260604_materias_estado.sql y las ocho consultas de
    `asignaciones_repository` lo adoptaron, pero estas dos se quedaron sin el.
    El resultado era que una asignatura desactivada desaparecia de todas las
    pantallas menos del boletin, que es justo donde mas se nota.
    """
    sql_repositorio = _sql_del_modulo("app/repositories/boletin_repository.py")
    filtro = "COALESCE(LOWER(m.estado), 'activo') = 'activo'"

    con_filtro = [sentencia for sentencia in sql_repositorio if filtro in sentencia]

    assert len(con_filtro) == 2
    assert all("FROM estudiantes e" in sentencia for sentencia in con_filtro)


def test_guardar_boletin_sin_detalles_borra_y_no_inserta_ninguno(monkeypatch):
    """El reemplazo parcial borra siempre, aunque el lote venga vacio."""
    cursor = CursorFalso(secuencia_fetchone=[(77,)])
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: None,
    )

    boletin_controller.guardar_boletin_controller(_BoletinFalso(detalles=[]))

    sentencias = [sql for sql, _ in cursor.calls]
    assert len(sentencias) == 2
    assert "DELETE FROM boletin_detalles" in sentencias[1]
    assert conn.commits == 1


# --------------------------------------------------------------------------
# Las cifras son el contrato
# --------------------------------------------------------------------------

def test_reporte_parcial_promedia_en_python_y_no_redondea(monkeypatch):
    """3,0 + 4,0 + 4,0 da 3,6666... y se devuelve SIN redondear.

    Es una cuarta forma de promediar en el programa y difiere de la de
    `notas`, que redondea a dos decimales con `round`.
    """
    filas = [
        {
            "asignacion_id": 44, "materia_id": 12, "materia": "Historia",
            "profesor_nombre": "Ana", "profesor_apellido": "Ruiz",
            "orden_boletin": 1, "nota_detalle_id": 101, "descripcion": "A",
            "nota": nota, "tipo_evaluacion": "numerica", "valoracion": None,
        }
        for nota in (3.0, 4.0, 4.0)
    ]
    for indice, fila in enumerate(filas):
        fila["nota_detalle_id"] = 101 + indice

    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        },
        filas=filas,
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    definitiva = resultado["materias"][0]["definitiva"]
    assert definitiva == pytest.approx(3.6666666666666665)
    assert definitiva != 3.67
    assert definitiva != 3.66


def test_reporte_parcial_excluye_desarrollo_y_notas_no_positivas(monkeypatch):
    filas = [
        {
            "asignacion_id": 44, "materia_id": 12, "materia": "Historia",
            "profesor_nombre": "Ana", "profesor_apellido": "Ruiz",
            "orden_boletin": 1, "nota_detalle_id": 101, "descripcion": "Valida",
            "nota": 4.0, "tipo_evaluacion": "numerica", "valoracion": None,
        },
        {
            "asignacion_id": 44, "materia_id": 12, "materia": "Historia",
            "profesor_nombre": "Ana", "profesor_apellido": "Ruiz",
            "orden_boletin": 1, "nota_detalle_id": 102, "descripcion": "Cero",
            "nota": 0.0, "tipo_evaluacion": "numerica", "valoracion": None,
        },
        {
            "asignacion_id": 44, "materia_id": 12, "materia": "Historia",
            "profesor_nombre": "Ana", "profesor_apellido": "Ruiz",
            "orden_boletin": 1, "nota_detalle_id": 103, "descripcion": "Cualitativa",
            "nota": 5.0, "tipo_evaluacion": "desarrollo", "valoracion": "Logrado",
        },
    ]
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        },
        filas=filas,
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    # Los tres detalles se devuelven; solo uno entra en la definitiva.
    assert len(resultado["materias"][0]["detalles"]) == 3
    assert resultado["materias"][0]["definitiva"] == 4.0


def test_el_dominio_usa_dos_formas_de_promediar_una_en_sql_y_otra_en_python():
    """Hallazgo registrado y NO corregido.

    El boletin de admin promedia con `AVG(...)` dentro de SQL, que tras 7.1 vive
    en el repositorio; el reporte parcial promedia en Python con `sum()/len()`,
    que sigue en el controlador porque es calculo y no persistencia.
    """
    sentencias = _sql_del_modulo("app/repositories/boletin_repository.py")
    assert any("AVG(nd.nota)" in sql for sql in sentencias)

    fuente_parcial = inspect.getsource(
        boletin_controller.obtener_reporte_parcial_admin_controller
    )
    assert "sum(valores) / len(valores)" in fuente_parcial
    assert "round(" not in fuente_parcial


# --------------------------------------------------------------------------
# Linea base de consultas y de conexiones
# --------------------------------------------------------------------------

def test_linea_base_de_consultas_del_boletin_de_admin(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
            "puesto": 1,
            "total": 20,
        },
        secuencia_fetchall=[
            # 1) materias del curso
            [
                {
                    "asignacion_id": 44, "materia_id": 12, "materia": "Historia",
                    "profesor_nombre": "Ana", "profesor_apellido": "Ruiz",
                    "definitiva": 4.0, "boletin_id": 900, "orden_boletin": 1,
                }
            ],
            # 2) detalles guardados, pedidos en lote con ANY
            [
                {
                    "asignacion_id": 44, "periodo": 2, "nota": 4.0,
                    "tipo_evaluacion": "numerica", "valoracion": None,
                    "observacion": "Buen desempeño", "detalle_idx": 1,
                }
            ],
        ],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert resultado["puesto"] == 1
    assert resultado["total_estudiantes"] == 20
    assert resultado["materias"][0]["definitiva"] == 4.0
    assert resultado["materias"][0]["detalles"][0]["observacion"] == "Buen desempeño"

    # 4 consultas fijas y NINGUN N+1: los detalles se piden con `= ANY(%s)`.
    # Coincide con la medicion de la capa 4, que conto 4 consultas para un
    # boletin de 13 materias.
    assert len(cursor.calls) == 4
    assert "= ANY(%s)" in cursor.calls[1][0]
    assert conn.closed is True


def test_boletin_de_admin_incluye_el_director_de_grupo_cuando_el_curso_tiene(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
            "director_grupo_nombre": "Ana",
            "director_grupo_apellido": "Gómez",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert resultado["director_grupo"] == "Ana Gómez"


def test_boletin_de_admin_sin_director_de_grupo_devuelve_none(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert resultado["director_grupo"] is None


def test_boletin_de_admin_incluye_la_jornada_del_curso(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
            "jornada": "Tarde",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_boletin_admin_controller(8, 2)

    assert resultado["jornada"] == "Tarde"


def test_linea_base_de_consultas_del_reporte_parcial(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    assert len(cursor.calls) == 2
    assert cursor.closed is True
    assert conn.closed is True


def test_reporte_parcial_incluye_el_director_de_grupo_cuando_el_curso_tiene(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
            "director_grupo_nombre": "Ana",
            "director_grupo_apellido": "Gómez",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    assert resultado["director_grupo"] == "Ana Gómez"


def test_reporte_parcial_sin_director_de_grupo_devuelve_none(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    assert resultado["director_grupo"] is None


def test_reporte_parcial_incluye_la_jornada_del_curso(monkeypatch):
    cursor = CursorFalso(
        una_fila={
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
            "jornada": "Tarde",
        },
        filas=[],
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    assert resultado["jornada"] == "Tarde"


def test_linea_base_de_consultas_de_referencia_para_profesor(monkeypatch):
    cursor = CursorFalso(
        secuencia_fetchall=[
            # 1) notas de la planilla vigente
            [
                {
                    "estudiante_id": 3, "nombre": "Sara", "apellido": "López",
                    "tipo_nota": "Parcial", "nota": 4.0,
                    "tipo_evaluacion": "numerica", "valoracion": None,
                }
            ],
            # 2) lo ya guardado en el boletin, en lote
            [
                {
                    "estudiante_id": 3, "definitiva": 4.0, "nota": 4.0,
                    "observacion": "Observación guardada",
                    "tipo_evaluacion": "numerica", "valoracion": None,
                }
            ],
        ]
    )
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: None,
    )

    resultado = boletin_controller.obtener_boletin_para_profesor_controller(44, 2)

    # El resolver esta doblado: quedan las 2 consultas propias del controlador,
    # la de la planilla y la del boletin guardado, esta ultima en lote con ANY.
    assert len(cursor.calls) == 2
    assert "= ANY(%s)" in cursor.calls[1][0]
    assert resultado[0]["notas"][0]["observacion_guardada"] == "Observación guardada"


def test_guardar_boletin_cuesta_tres_consultas_mas_una_por_detalle(monkeypatch):
    cursor = CursorFalso(secuencia_fetchone=[(77,)])
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: None,
    )

    detalles = [_DetalleFalso() for _ in range(5)]
    boletin_controller.guardar_boletin_controller(_BoletinFalso(detalles=detalles))

    # 2 fijas dentro del controlador + 1 INSERT por detalle. Los dos resolvers
    # (asignacion academica y nivel del curso) estan doblados, asi que no
    # suman aqui; en produccion, con el nivel academico, son 4 + N.
    assert len(cursor.calls) == 2 + len(detalles)


def test_linea_base_de_conexiones_por_entrada(monkeypatch):
    """El dominio NO repite el N+1 en conexiones que dejo `asistencia`.

    `require_estudiante_in_asignacion` se llama UNA vez, fuera de todo bucle,
    asi que el coste no crece con el numero de estudiantes.
    """
    contador_permisos = ContadorDeConexiones()
    monkeypatch.setattr(permissions, "get_connection", contador_permisos)

    # Admin: `require_asignacion_access` retorna antes de conectar.
    permissions.require_asignacion_access(44, {"rol": "admin", "id": 1})
    assert contador_permisos.abiertas == 0

    permissions.require_estudiante_in_asignacion(8, 44)
    assert contador_permisos.abiertas == 1

    # Profesor: si conecta para comprobar la asignacion.
    permissions.require_asignacion_access(44, {"rol": "profesor", "id": 7})
    assert contador_permisos.abiertas == 2


def test_cada_controlador_abre_exactamente_una_conexion(monkeypatch):
    contador = ContadorDeConexiones()
    monkeypatch.setattr(boletin_controller, "get_connection", contador)
    monkeypatch.setattr(
        boletin_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 55,
    )
    monkeypatch.setattr(
        boletin_controller,
        "resolver_nivel_curso_cursor",
        lambda _cursor, _asignacion_id: None,
    )

    boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)
    assert contador.abiertas == 1

    boletin_controller.obtener_boletin_para_profesor_controller(44, 2)
    assert contador.abiertas == 2


# --------------------------------------------------------------------------
# Contratos HTTP: permisos y status codes
# --------------------------------------------------------------------------

def test_las_cuatro_entradas_conservan_sus_tres_modelos_de_permiso():
    fuente = (RAIZ / "app/routes/boletines.py").read_text(encoding="utf-8")

    # Guard de router para todas.
    assert "dependencies=[Depends(get_current_user)]" in fuente

    # Solo la escritura comprueba la pertenencia del estudiante, y una sola vez.
    assert fuente.count("require_estudiante_in_asignacion(") == 1
    # Escritura y referencia comprueban acceso a la asignacion.
    assert fuente.count("require_asignacion_access(") == 2
    # Las dos entradas de admin usan el guard administrativo.
    assert fuente.count("Depends(get_current_active_admin)") == 2


def test_los_permisos_se_evaluan_fuera_del_try_y_el_403_no_se_convierte_en_500(monkeypatch):
    """Contraste con `dashboard`: alli una consulta de permiso dentro del
    `try` salia como 500. Aqui los guards corren antes."""
    def negar(_estudiante_id, _asignacion_id):
        raise HTTPException(status_code=403, detail="El estudiante no pertenece a esta asignación")

    monkeypatch.setattr(boletines, "require_asignacion_access", lambda *_a, **_k: None)
    monkeypatch.setattr(boletines, "require_estudiante_in_asignacion", negar)

    with pytest.raises(HTTPException) as exc:
        boletines.guardar_boletin(_BoletinFalso(), {"rol": "profesor", "id": 7})

    assert exc.value.status_code == 403


def test_las_cuatro_entradas_mapean_el_fallo_a_500_sin_filtrar_el_texto(monkeypatch):
    """Hallazgo favorable y poco frecuente en el programa: este dominio NO
    devuelve el texto de la excepcion al cliente."""
    def estallar(*_args, **_kwargs):
        raise RuntimeError("detalle interno que no debe salir")

    monkeypatch.setattr(boletines, "require_asignacion_access", lambda *_a, **_k: None)
    monkeypatch.setattr(boletines, "require_estudiante_in_asignacion", lambda *_a, **_k: None)
    monkeypatch.setattr(boletines, "guardar_boletin_controller", estallar)
    monkeypatch.setattr(boletines, "obtener_boletin_para_profesor_controller", estallar)
    monkeypatch.setattr(boletines, "obtener_boletin_admin_controller", estallar)
    monkeypatch.setattr(boletines, "obtener_reporte_parcial_admin_controller", estallar)

    llamadas = [
        (boletines.guardar_boletin, (_BoletinFalso(), {"rol": "admin"}),
         "No se pudo guardar el boletin"),
        (boletines.obtener_notas_referencia, (44, 2, {"rol": "admin"}),
         "No se pudieron obtener las notas"),
        (boletines.generar_boletin_admin, (8, 2, {"rol": "admin"}),
         "No se pudo generar el boletin"),
        (boletines.generar_reporte_parcial_admin, (8, 2, {"rol": "admin"}),
         "No se pudo generar el reporte parcial"),
    ]

    for funcion, args, detalle in llamadas:
        with pytest.raises(HTTPException) as exc:
            funcion(*args)
        assert exc.value.status_code == 500
        assert exc.value.detail == detalle
        assert "detalle interno" not in str(exc.value.detail)


def test_las_dos_entradas_admin_responden_404_con_resultado_vacio(monkeypatch):
    # Año lectivo, fase 3 (paso 3.5a): los controladores reciben el año.
    monkeypatch.setattr(
        boletines, "obtener_boletin_admin_controller", lambda *_a, **_k: None
    )
    monkeypatch.setattr(
        boletines, "obtener_reporte_parcial_admin_controller", lambda *_a, **_k: None
    )

    for funcion in (boletines.generar_boletin_admin,
                    boletines.generar_reporte_parcial_admin):
        with pytest.raises(HTTPException) as exc:
            funcion(999, 1, {"rol": "admin"})
        assert exc.value.status_code == 404
        assert exc.value.detail == "Estudiante no encontrado"


def test_el_404_no_queda_atrapado_por_el_except_generico(monkeypatch):
    """Las dos entradas admin reenvian `HTTPException` antes del `except
    Exception`. Sin ese reenvio, el 404 se convertiria en 500."""
    fuente = (RAIZ / "app/routes/boletines.py").read_text(encoding="utf-8")
    assert fuente.count("except HTTPException:") == 2
