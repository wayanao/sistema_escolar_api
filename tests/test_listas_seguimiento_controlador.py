"""Paso 4 de "Listas de Seguimiento por Curso": el controlador.

Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`. Fija lo que puede romperse
sin que nadie lo note:

- que **no conoce HTTP**: lanza errores propios y no `HTTPException`;
- que el duplicado se atrapa **dos veces**, porque entre preguntar y escribir
  hay una ventana por la que otra peticion puede colarse;
- que el lote se valida **entero antes de escribir nada**, para que no quede
  media pantalla guardada;
- cuantas consultas y cuantas conexiones cuesta cada operacion, que es lo que
  se degrada en silencio.

El repositorio se sustituye por uno falso: el de verdad ya tiene sus propias
35 pruebas, y aqui lo que se mira es la logica del controlador.
"""
from contextlib import contextmanager

import pytest
from psycopg2 import IntegrityError

from app.controllers import listas_seguimiento_controller as controlador
from app.controllers.listas_seguimiento_controller import (
    ColumnaDuplicadaError,
    ColumnaNoEncontradaError,
    CursoNoEncontradoError,
    MarcasFueraDelCursoError,
)
from app.schemas.listas_seguimiento import MarcaSeguimientoItem


COLUMNAS = [(5, "Asistio a la cumbre"), (6, "Compro el libro")]
ESTUDIANTES = [(101, "Juan", "Perez"), (102, "Ana", "Rojas")]
MARCAS = [(5, 101, True, "Llego tarde")]


def celda(columna_id=5, estudiante_id=101, marcado=True, nota=""):
    return MarcaSeguimientoItem(
        columna_id=columna_id,
        estudiante_id=estudiante_id,
        marcado=marcado,
        nota=nota,
    )


class RepositorioFalso:
    """Anota que se le pide y devuelve lo que el test le haya puesto."""

    def __init__(
        self,
        curso_existe=True,
        columnas=COLUMNAS,
        estudiantes=ESTUDIANTES,
        marcas=MARCAS,
        nombre_ocupado=False,
        borro=True,
        guardadas=0,
        error_al_crear=None,
        cursos_activos=25,
        creadas_masivas=0,
    ):
        self.cursos_activos = cursos_activos
        self.creadas_masivas = creadas_masivas
        self.curso_existe = curso_existe
        self.columnas = list(columnas)
        self.estudiantes = list(estudiantes)
        self.marcas = list(marcas)
        self.nombre_ocupado = nombre_ocupado
        self.borro = borro
        self.guardadas = guardadas
        self.error_al_crear = error_al_crear
        self.llamadas = []

    def _anotar(self, nombre, *args):
        self.llamadas.append((nombre,) + args)

    @property
    def nombres_llamados(self):
        return [llamada[0] for llamada in self.llamadas]

    def existe_curso(self, cursor, curso_id):
        self._anotar("existe_curso", curso_id)
        return self.curso_existe

    def leer_columnas_del_curso(self, cursor, curso_id):
        self._anotar("leer_columnas_del_curso", curso_id)
        return self.columnas

    def leer_estudiantes_del_curso(self, cursor, curso_id):
        self._anotar("leer_estudiantes_del_curso", curso_id)
        return self.estudiantes

    def leer_marcas_de_columnas(self, cursor, columna_ids):
        self._anotar("leer_marcas_de_columnas", list(columna_ids))
        return self.marcas if columna_ids else []

    def existe_columna_con_ese_nombre(self, cursor, curso_id, nombre):
        self._anotar("existe_columna_con_ese_nombre", curso_id, nombre)
        return self.nombre_ocupado

    def crear_columna(self, cursor, curso_id, nombre):
        self._anotar("crear_columna", curso_id, nombre)
        if self.error_al_crear:
            raise self.error_al_crear
        return 7

    # Año lectivo, fase 3 (paso 3.3): las dos reciben el año. Aqui no se
    # anota porque estas pruebas no tratan del año; lo cubre
    # test_anio_lectivo_lecturas.py.
    def contar_cursos_activos(self, cursor, anio_lectivo_id=None):
        self._anotar("contar_cursos_activos")
        return self.cursos_activos

    def crear_columna_en_cursos_activos(self, cursor, nombre, anio_lectivo_id=None):
        self._anotar("crear_columna_en_cursos_activos", nombre)
        if self.error_al_crear:
            raise self.error_al_crear
        return self.creadas_masivas

    def eliminar_columna(self, cursor, curso_id, columna_id):
        self._anotar("eliminar_columna", curso_id, columna_id)
        return self.borro

    def guardar_marcas(self, cursor, marcas):
        self._anotar("guardar_marcas", list(marcas))
        return self.guardadas


class ContadorDeConexiones:
    """Cuenta cuantas veces se pide una conexion y con que `commit`."""

    def __init__(self):
        self.abiertas = 0
        self.commits = []

    @contextmanager
    def __call__(self, commit=False, cursor_factory=None):
        self.abiertas += 1
        self.commits.append(commit)
        yield "cursor-falso"


@pytest.fixture(autouse=True)
def guardia_del_anio(monkeypatch):
    """Año lectivo, paso 3.7: la guardia de escritura se dobla aqui, igual que
    el repositorio. Sus pruebas viven en `test_anio_lectivo_guardia.py` y la
    cuenta `test_anio_lectivo_guardia_conteos.py`; aqui solo se anota sobre que
    cursos se pidio."""
    llamadas = []
    monkeypatch.setattr(
        controlador,
        "exigir_cursos_editables_para_admin",
        lambda _cursor, curso_ids: llamadas.append(list(curso_ids)),
    )
    return llamadas


@pytest.fixture
def entorno(monkeypatch):
    def montar(**kwargs):
        repo = RepositorioFalso(**kwargs)
        conexiones = ContadorDeConexiones()
        monkeypatch.setattr(controlador, "repositorio", repo)
        monkeypatch.setattr(controlador, "get_cursor", conexiones)
        return repo, conexiones

    return montar


# ---------------------------------------------------------------------------
# La capa: el controlador no habla HTTP.
# ---------------------------------------------------------------------------


def test_no_conoce_fastapi():
    """Lanza errores propios; traducirlos a codigos es trabajo de la ruta.

    Si alguien mete un `HTTPException` aqui, el controlador deja de poder
    usarse desde cualquier otro sitio y las pruebas de dominio empiezan a
    depender de codigos de estado.
    """
    prohibidos = {"HTTPException", "APIRouter", "status", "Depends"}
    assert not (prohibidos & set(dir(controlador)))


# ---------------------------------------------------------------------------
# Armar la respuesta: funcion pura, sin base de datos.
# ---------------------------------------------------------------------------


def test_la_respuesta_tiene_la_forma_del_documento():
    respuesta = controlador._armar_respuesta(12, COLUMNAS, ESTUDIANTES, MARCAS)

    assert respuesta == {
        "curso_id": 12,
        "columnas": [
            {"id": 5, "nombre": "Asistio a la cumbre"},
            {"id": 6, "nombre": "Compro el libro"},
        ],
        "estudiantes": [
            {
                "estudiante_id": 101,
                "nombre": "Juan",
                "apellido": "Perez",
                "marcas": {"5": {"marcado": True, "nota": "Llego tarde"}},
            },
            {
                "estudiante_id": 102,
                "nombre": "Ana",
                "apellido": "Rojas",
                "marcas": {},
            },
        ],
    }


def test_las_claves_de_marcas_son_texto():
    """JSON solo admite claves de texto. Se pone explicito para que el objeto
    de Python y lo que ve el navegador sean iguales, no parecidos."""
    respuesta = controlador._armar_respuesta(12, COLUMNAS, ESTUDIANTES, MARCAS)
    claves = respuesta["estudiantes"][0]["marcas"].keys()

    assert all(isinstance(clave, str) for clave in claves)


def test_una_nota_nula_sale_como_cadena_vacia():
    """Una fila escrita fuera de esta pantalla puede tener NULL; el frontend
    espera texto."""
    respuesta = controlador._armar_respuesta(
        12, COLUMNAS, ESTUDIANTES, [(5, 101, False, None)]
    )

    assert respuesta["estudiantes"][0]["marcas"]["5"] == {
        "marcado": False,
        "nota": "",
    }


def test_la_marca_de_un_alumno_que_ya_no_esta_no_se_pinta():
    """Si lo trasladaron de curso, su fila sigue en la base pero no tiene
    donde salir. No se borra nada por esto."""
    respuesta = controlador._armar_respuesta(
        12, COLUMNAS, ESTUDIANTES, [(5, 999, True, "de otro curso")]
    )

    assert all(alumno["marcas"] == {} for alumno in respuesta["estudiantes"])


# ---------------------------------------------------------------------------
# GET: la lista completa.
# ---------------------------------------------------------------------------


def test_un_curso_inexistente_no_se_sigue_consultando(entorno):
    repo, conexiones = entorno(curso_existe=False)

    with pytest.raises(CursoNoEncontradoError):
        controlador.obtener_lista_seguimiento_controller(12)

    assert repo.nombres_llamados == ["existe_curso"]
    assert conexiones.abiertas == 1


def test_la_lista_completa_cuesta_cuatro_consultas_y_una_conexion(entorno):
    repo, conexiones = entorno()

    controlador.obtener_lista_seguimiento_controller(12)

    assert repo.nombres_llamados == [
        "existe_curso",
        "leer_columnas_del_curso",
        "leer_estudiantes_del_curso",
        "leer_marcas_de_columnas",
    ]
    assert conexiones.abiertas == 1
    assert conexiones.commits == [False]


def test_un_curso_sin_columnas_no_pregunta_por_las_marcas(entorno):
    """Tres consultas en vez de cuatro. Sin columnas no hay marcas posibles."""
    repo, _ = entorno(columnas=[])

    respuesta = controlador.obtener_lista_seguimiento_controller(12)

    assert repo.nombres_llamados[-1] == "leer_marcas_de_columnas"
    assert repo.llamadas[-1] == ("leer_marcas_de_columnas", [])
    assert respuesta["columnas"] == []
    assert len(respuesta["estudiantes"]) == 2


def test_un_curso_sin_columnas_no_es_un_error(entorno):
    """Es la pantalla recien estrenada. Lo fija el documento como invariante."""
    entorno(columnas=[], marcas=[])

    respuesta = controlador.obtener_lista_seguimiento_controller(12)

    assert respuesta["curso_id"] == 12
    assert respuesta["estudiantes"][0]["marcas"] == {}


# ---------------------------------------------------------------------------
# Crear columna.
# ---------------------------------------------------------------------------


def test_no_se_crea_una_columna_en_un_curso_inexistente(entorno):
    """Sin esta comprobacion reventaria contra la clave foranea, y eso llega
    al usuario como un 500 en vez de un 404."""
    repo, _ = entorno(curso_existe=False)

    with pytest.raises(CursoNoEncontradoError):
        controlador.crear_columna_controller(12, "Nueva")

    assert "crear_columna" not in repo.nombres_llamados


def test_un_nombre_ya_usado_se_rechaza_antes_de_insertar(entorno):
    repo, _ = entorno(nombre_ocupado=True)

    with pytest.raises(ColumnaDuplicadaError):
        controlador.crear_columna_controller(12, "Ya existe")

    assert "crear_columna" not in repo.nombres_llamados


def test_la_carrera_por_el_mismo_nombre_tambien_da_duplicado(entorno):
    """Dos pestanas, o un doble clic: la consulta previa dice que el nombre
    esta libre y el indice unico rechaza el INSERT.

    Sin este segundo `except`, esa carrera saldria como 500.
    """
    repo, _ = entorno(nombre_ocupado=False, error_al_crear=IntegrityError("duplicada"))

    with pytest.raises(ColumnaDuplicadaError):
        controlador.crear_columna_controller(12, "Nueva")

    assert "crear_columna" in repo.nombres_llamados


def test_el_error_de_duplicado_no_filtra_el_mensaje_de_postgresql(entorno):
    """El frontend muestra este texto tal cual. `str(exc)` de un IntegrityError
    pondria nombres de tablas e indices en la pantalla."""
    entorno(error_al_crear=IntegrityError('llave duplicada viola restriccion "idx_..."'))

    with pytest.raises(ColumnaDuplicadaError) as error:
        controlador.crear_columna_controller(12, "Nueva")

    assert str(error.value) == controlador.COLUMNA_DUPLICADA
    assert "idx_" not in str(error.value)


def test_crear_una_columna_devuelve_su_id_y_confirma(entorno):
    repo, conexiones = entorno()

    assert controlador.crear_columna_controller(12, "Nueva") == 7
    assert repo.llamadas[-1] == ("crear_columna", 12, "Nueva")
    assert conexiones.commits == [True]


# ---------------------------------------------------------------------------
# Borrar columna.
# ---------------------------------------------------------------------------


def test_borrar_cuesta_una_sola_consulta(entorno):
    """El repositorio acota por curso dentro del propio DELETE, asi que no
    hace falta preguntar antes si el curso existe."""
    repo, conexiones = entorno()

    controlador.eliminar_columna_controller(12, 5)

    assert repo.nombres_llamados == ["eliminar_columna"]
    assert repo.llamadas[0] == ("eliminar_columna", 12, 5)
    assert conexiones.commits == [True]


def test_borrar_una_columna_ajena_o_inexistente_da_el_mismo_error(entorno):
    entorno(borro=False)

    with pytest.raises(ColumnaNoEncontradaError):
        controlador.eliminar_columna_controller(12, 5)


# ---------------------------------------------------------------------------
# Guardar el lote de marcas.
# ---------------------------------------------------------------------------


def test_una_columna_de_otro_curso_invalida_el_lote(entorno):
    repo, _ = entorno()

    with pytest.raises(MarcasFueraDelCursoError):
        controlador.guardar_marcas_controller(12, [celda(columna_id=999)])

    assert "guardar_marcas" not in repo.nombres_llamados


def test_un_alumno_de_otro_curso_invalida_el_lote(entorno):
    repo, _ = entorno()

    with pytest.raises(MarcasFueraDelCursoError):
        controlador.guardar_marcas_controller(12, [celda(estudiante_id=999)])

    assert "guardar_marcas" not in repo.nombres_llamados


def test_una_celda_mala_impide_guardar_todo_el_lote(entorno):
    """O entra todo o no entra nada. Guardando lo bueno y descartando lo malo,
    el usuario se quedaria con media pantalla escrita y sin saber cual."""
    repo, _ = entorno()
    lote = [celda(estudiante_id=101), celda(estudiante_id=102), celda(columna_id=999)]

    with pytest.raises(MarcasFueraDelCursoError):
        controlador.guardar_marcas_controller(12, lote)

    assert "guardar_marcas" not in repo.nombres_llamados


def test_el_error_del_lote_no_dice_cual_celda_sobra(entorno):
    """Mensaje constante: el frontend lo muestra tal cual."""
    entorno()

    with pytest.raises(MarcasFueraDelCursoError) as error:
        controlador.guardar_marcas_controller(12, [celda(columna_id=999)])

    assert str(error.value) == controlador.MARCAS_FUERA_DEL_CURSO


def test_guardar_no_pregunta_aparte_si_el_curso_existe(entorno):
    """Un curso inventado no tiene columnas ni alumnos, asi que la primera
    celda ya queda fuera y sale el 422 que el documento pide para este
    endpoint. Una consulta menos."""
    repo, _ = entorno(curso_existe=False, columnas=[], estudiantes=[])

    with pytest.raises(MarcasFueraDelCursoError):
        controlador.guardar_marcas_controller(12, [celda()])

    assert "existe_curso" not in repo.nombres_llamados


def test_el_lote_valido_llega_al_repositorio_como_tuplas(entorno):
    repo, conexiones = entorno(guardadas=2)
    lote = [
        celda(columna_id=5, estudiante_id=101, marcado=True, nota="Llego tarde"),
        celda(columna_id=6, estudiante_id=102, marcado=False, nota=""),
    ]

    assert controlador.guardar_marcas_controller(12, lote) == 2
    assert repo.llamadas[-1] == (
        "guardar_marcas",
        [(5, 101, True, "Llego tarde"), (6, 102, False, "")],
    )
    assert conexiones.commits == [True]


def test_leer_validar_y_escribir_ocurren_en_la_misma_conexion(entorno, guardia_del_anio):
    """Si se validara en una conexion y se escribiera en otra, entre las dos
    podrian borrar la columna que se acaba de dar por buena."""
    repo, conexiones = entorno(guardadas=1)

    controlador.guardar_marcas_controller(12, [celda()])

    assert repo.nombres_llamados == [
        "leer_columnas_del_curso",
        "leer_estudiantes_del_curso",
        "guardar_marcas",
    ]
    assert conexiones.abiertas == 1
    # Y la guardia del año lectivo (paso 3.7), sobre ese curso y en esa misma
    # conexion: es la unica que se abrio.
    assert guardia_del_anio == [[12]]


# ---------------------------------------------------------------------------
# El `return` desde dentro del `with`: lo unico que los dobles de arriba no
# pueden comprobar.
# ---------------------------------------------------------------------------


def test_devolver_desde_dentro_del_with_confirma_la_transaccion(monkeypatch):
    """`crear_columna_controller` y `guardar_marcas_controller` devuelven su
    resultado **desde dentro** del `with get_cursor(commit=True)`.

    Si eso no confirmara la transaccion, crear una columna no guardaria nada y
    todas las pruebas de este archivo seguirian en verde: el `get_cursor` falso
    de arriba solo anota con que valor de `commit` se le llamo, no si alguien
    lo honra.

    `tests/test_db_session_contrato.py` cubre el `with` que termina solo y el
    que termina en excepcion. Este caso no estaba, y la suposicion es de este
    modulo, asi que la guarda vive aqui.
    """
    from app.db import session

    class CursorInerte:
        def close(self):
            pass

    class ConexionEspia:
        def __init__(self):
            self.commits = 0
            self.rollbacks = 0

        def cursor(self, cursor_factory=None):
            return CursorInerte()

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

        def close(self):
            pass

    espia = ConexionEspia()
    monkeypatch.setattr(session, "get_connection", lambda: espia)

    def devuelve_desde_dentro():
        with session.get_cursor(commit=True) as cursor:
            assert cursor is not None
            return "listo"

    assert devuelve_desde_dentro() == "listo"
    assert espia.commits == 1
    assert espia.rollbacks == 0


# ---------------------------------------------------------------------------
# Ampliacion: crear la columna en todos los cursos.
#
# Ver docs/funcionalidades/LISTAS_SEGUIMIENTO.md, seccion "Ampliacion".
# ---------------------------------------------------------------------------


def test_el_alta_masiva_devuelve_creadas_omitidas_y_total(entorno):
    repo, conexiones = entorno(cursos_activos=25, creadas_masivas=9)

    assert controlador.crear_columna_en_todos_los_cursos_controller("Excursion") == {
        "creadas": 9,
        "omitidas": 16,
        "total": 25,
    }
    assert conexiones.abiertas == 1
    assert conexiones.commits == [True]


def test_el_alta_masiva_crea_antes_de_contar(entorno):
    """Al reves, un curso creado por otra persona entre las dos consultas
    entraria en el alta pero no en el conteo, `creadas` podria superar a
    `total` y la pantalla mostraria un numero negativo de omitidas."""
    repo, _ = entorno(cursos_activos=25, creadas_masivas=9)

    controlador.crear_columna_en_todos_los_cursos_controller("Excursion")

    assert repo.nombres_llamados == [
        "crear_columna_en_cursos_activos",
        "contar_cursos_activos",
    ]


def test_las_omitidas_nunca_salen_en_negativo(entorno):
    """Ultimo resquicio: que alguien borre un curso justo entre las dos
    consultas. No arregla ninguna logica, impide un numero imposible."""
    entorno(cursos_activos=3, creadas_masivas=5)

    resultado = controlador.crear_columna_en_todos_los_cursos_controller("Excursion")

    assert resultado["omitidas"] == 0


def test_no_crear_ninguna_no_es_un_error(entorno):
    """Si todos los cursos ya la tenian, `creadas` vale 0 y la respuesta es un
    exito. Es la consecuencia de que el alta salte en silencio los que ya la
    tienen, que es lo que vuelve repetible el boton."""
    entorno(cursos_activos=25, creadas_masivas=0)

    resultado = controlador.crear_columna_en_todos_los_cursos_controller("Excursion")

    assert resultado == {"creadas": 0, "omitidas": 25, "total": 25}


def test_un_colegio_sin_cursos_activos_no_revienta(entorno):
    entorno(cursos_activos=0, creadas_masivas=0)

    assert controlador.crear_columna_en_todos_los_cursos_controller("Excursion") == {
        "creadas": 0,
        "omitidas": 0,
        "total": 0,
    }


def test_el_nombre_llega_tal_cual_al_repositorio(entorno):
    repo, _ = entorno(creadas_masivas=1)

    controlador.crear_columna_en_todos_los_cursos_controller("Pago la excursion")

    assert repo.llamadas[0] == ("crear_columna_en_cursos_activos", "Pago la excursion")


def test_la_carrera_del_indice_no_sale_como_500(entorno):
    """Dos peticiones a la vez: el NOT EXISTS de las dos dice que falta y quien
    rechaza es el indice unico. Reintentar funciona, porque a la segunda el
    NOT EXISTS ya la ve."""
    entorno(error_al_crear=IntegrityError("llave duplicada"))

    with pytest.raises(ColumnaDuplicadaError) as error:
        controlador.crear_columna_en_todos_los_cursos_controller("Excursion")

    assert str(error.value) == controlador.ALTA_MASIVA_EN_CARRERA


def test_la_carrera_lleva_su_propio_mensaje_no_el_de_ya_existe(entorno):
    """El usuario pidio rellenar los cursos que faltaran, no crear una sola
    columna: decirle "ya existe" no describe lo que paso."""
    entorno(error_al_crear=IntegrityError("llave duplicada"))

    with pytest.raises(ColumnaDuplicadaError) as error:
        controlador.crear_columna_en_todos_los_cursos_controller("Excursion")

    assert str(error.value) != controlador.COLUMNA_DUPLICADA
    assert "duplicada" not in str(error.value)
