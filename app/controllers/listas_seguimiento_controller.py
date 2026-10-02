"""Reglas de Listas de Seguimiento. Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`.

Este modulo **no conoce HTTP**: lanza errores propios y es la ruta la que los
traduce a 404, 409 o 422, igual que hace `curso_controller` con
`CursoDuplicadoError`.

Los mensajes de esos errores son **constantes** y nunca llevan el texto de
PostgreSQL dentro. El frontend los muestra tal cual, y `str(exc)` de un error
de base de datos pondria nombres de tablas e indices en la pantalla de una
secretaria. Es la leccion que dejo escrita `app/routes/observador.py`.

Cada funcion abre **una sola** conexion para todo lo que hace. Contra Neon
cada ida y vuelta cuesta ~180 ms, asi que lo que se cuenta son las consultas:

- `obtener_lista_seguimiento_controller`: 4 -existe el curso, columnas,
  alumnos, marcas-, o 3 si el curso no tiene columnas. **Ese numero es fijo:
  no crece con la cantidad de alumnos ni de columnas.** Es justo lo que la
  pantalla vieja del observador hacia mal.
- `crear_columna_controller`: 3. `eliminar_columna_controller`: 1.
  `guardar_marcas_controller`: 3.

En las escrituras, comprobar y escribir van **dentro de la misma
transaccion**. Si se validara en una conexion y se escribiera en otra, entre
las dos podrian borrar la columna que se acaba de dar por buena.
"""
from psycopg2 import IntegrityError

from app.database import get_cursor
from app.repositories import listas_seguimiento_repository as repositorio
from app.services.anio_lectivo import exigir_anio_lectivo


CURSO_NO_ENCONTRADO = "Ese curso no existe."
COLUMNA_DUPLICADA = "Ya existe una columna con ese nombre en este curso."
COLUMNA_NO_ENCONTRADA = "Esa columna ya no existe."
ALTA_MASIVA_EN_CARRERA = (
    "Otra persona estaba creando esa misma columna. Vuelve a intentarlo."
)
MARCAS_FUERA_DEL_CURSO = (
    "El lote incluye una columna o un estudiante que no son de este curso."
)


class CursoNoEncontradoError(Exception):
    """El curso de la URL no existe. La ruta lo traduce a 404."""


class ColumnaDuplicadaError(Exception):
    """Ese curso ya tiene una columna con ese nombre. La ruta lo traduce a 409."""


class ColumnaNoEncontradaError(Exception):
    """La columna no existe o no es de ese curso. La ruta lo traduce a 404."""


class MarcasFueraDelCursoError(ValueError):
    """El lote referencia algo ajeno al curso. La ruta lo traduce a 422."""


def _armar_respuesta(curso_id, columnas, estudiantes, marcas):
    """Junta las tres lecturas en la forma que consume el frontend.

    Funcion pura: no toca la base. Todo el trabajo es sobre memoria y queda
    fuera del bloque que ocupa la conexion.

    Las claves de `marcas` van como **texto** y no como numero. JSON solo
    admite claves de texto, asi que un diccionario con claves enteras saldria
    igual por el cable; ponerlo explicito evita que el objeto de Python y el
    JSON que ve el navegador se parezcan pero no sean iguales, que es la clase
    de diferencia que se descubre tarde y en una prueba ajena.

    Un alumno sin fila para una columna **no aparece** en su diccionario de
    marcas. El default (`marcado: false`, `nota: ""`) lo pone el frontend,
    igual que ya hace con las notas ausentes de la planilla.

    Una marca de un alumno que ya no esta en el curso -porque lo trasladaron-
    simplemente no se pinta: se arma por alumno del curso, y el que no esta en
    la lista no tiene fila donde salir. La fila sigue en la base; no se borra
    nada por esto.
    """
    por_estudiante = {}
    for columna_id, estudiante_id, marcado, nota in marcas:
        celdas = por_estudiante.setdefault(estudiante_id, {})
        celdas[str(columna_id)] = {"marcado": bool(marcado), "nota": nota or ""}

    return {
        "curso_id": curso_id,
        "columnas": [
            {"id": columna_id, "nombre": nombre} for columna_id, nombre in columnas
        ],
        "estudiantes": [
            {
                "estudiante_id": estudiante_id,
                "nombre": nombre,
                "apellido": apellido,
                "marcas": por_estudiante.get(estudiante_id, {}),
            }
            for estudiante_id, nombre, apellido in estudiantes
        ],
    }


def obtener_lista_seguimiento_controller(curso_id):
    """Columnas, alumnos y marcas de un curso, en una sola respuesta.

    Un curso que existe pero no tiene columnas devuelve sus alumnos y la lista
    de columnas vacia. No es un error: es la pantalla recien estrenada, y el
    documento lo fija como invariante.
    """
    with get_cursor() as cursor:
        if not repositorio.existe_curso(cursor, curso_id):
            raise CursoNoEncontradoError(CURSO_NO_ENCONTRADO)

        columnas = repositorio.leer_columnas_del_curso(cursor, curso_id)
        estudiantes = repositorio.leer_estudiantes_del_curso(cursor, curso_id)
        marcas = repositorio.leer_marcas_de_columnas(
            cursor, [columna_id for columna_id, _ in columnas]
        )

    return _armar_respuesta(curso_id, columnas, estudiantes, marcas)


def crear_columna_controller(curso_id, nombre):
    """Crea una columna en ese curso y devuelve su id.

    Comprueba que el curso exista **antes** de insertar. Sin eso, un curso
    inventado no daria un 404 sino que reventaria contra la clave foranea, y
    eso llega al usuario como un 500.

    **El duplicado se atrapa dos veces, y las dos hacen falta.** La consulta
    previa da el 409 en el caso normal, con un mensaje claro. Pero entre esa
    consulta y el `INSERT` hay una ventana por la que otra peticion puede
    colarse -dos pestanas, un doble clic-, y ahi quien rechaza es el indice
    unico de la tabla. Sin el segundo `except`, esa carrera saldria como 500.
    Es el mismo par que ya usa `crear_curso_controller`.

    `nombre` llega ya recortado por `ColumnaSeguimientoCreate`.
    """
    try:
        with get_cursor(commit=True) as cursor:
            if not repositorio.existe_curso(cursor, curso_id):
                raise CursoNoEncontradoError(CURSO_NO_ENCONTRADO)

            if repositorio.existe_columna_con_ese_nombre(cursor, curso_id, nombre):
                raise ColumnaDuplicadaError(COLUMNA_DUPLICADA)

            return repositorio.crear_columna(cursor, curso_id, nombre)
    except IntegrityError as exc:
        raise ColumnaDuplicadaError(COLUMNA_DUPLICADA) from exc


def crear_columna_en_todos_los_cursos_controller(nombre, anio_lectivo_id=None):
    """Crea la columna en los cursos activos de un año que aun no la tengan.

    Sin `anio_lectivo_id`, los del año activo (fase 3 del año lectivo). Un año
    que no existe lanza `ValueError` antes de escribir nada.

    Devuelve `{"creadas", "omitidas", "total"}`, que es lo que la pantalla
    necesita para decir algo honesto: "Creada en 9 cursos. 2 ya la tenian."

    **Crear que no crea nada NO es un error.** Si todos los cursos ya la
    tenian, `creadas` vale 0 y la respuesta es un exito. Es la consecuencia de
    que el alta salte en silencio los que ya la tienen, que es justo lo que
    vuelve repetible el boton. Un colegio sin cursos activos tampoco falla:
    devuelve todo a cero.

    **El orden importa: primero se crea y despues se cuenta.** Al reves, un
    curso creado por otra persona entre las dos consultas entraria en el alta
    pero no en el conteo, `creadas` podria superar a `total` y la pantalla
    mostraria un numero **negativo** de omitidas. Haciendolo en este orden,
    todo curso en el que se inserto existe y esta activo cuando se cuenta, asi
    que `creadas` nunca pasa de `total`. El `max(..., 0)` cubre el ultimo
    resquicio -que alguien borre un curso justo en medio-: no arregla ninguna
    logica, solo impide que salga un numero imposible en pantalla.

    **La carrera del indice se trata aparte.** Si dos peticiones entran a la
    vez, el `NOT EXISTS` de las dos puede decir que falta y quien rechaza es el
    indice unico. Eso no es "ya existe esa columna" -el usuario pidio
    rellenar, no crear una sola-, asi que lleva su propio mensaje y su propia
    salida: reintentar funciona, porque a la segunda el `NOT EXISTS` ya la ve.
    Sin este `except` seria un 500.
    """
    try:
        with get_cursor(commit=True) as cursor:
            if anio_lectivo_id is not None:
                exigir_anio_lectivo(cursor, anio_lectivo_id)
            creadas = repositorio.crear_columna_en_cursos_activos(
                cursor, nombre, anio_lectivo_id=anio_lectivo_id
            )
            total = repositorio.contar_cursos_activos(
                cursor, anio_lectivo_id=anio_lectivo_id
            )

            return {
                "creadas": creadas,
                "omitidas": max(total - creadas, 0),
                "total": total,
            }
    except IntegrityError as exc:
        raise ColumnaDuplicadaError(ALTA_MASIVA_EN_CARRERA) from exc


def eliminar_columna_controller(curso_id, columna_id):
    """Borra la columna y, en cascada, todas sus marcas.

    Una sola consulta: el repositorio acota por curso dentro del propio
    `DELETE`, asi que no hace falta preguntar antes si el curso existe. Un
    curso inventado y una columna de otro curso acaban los dos en el mismo
    404, que es la respuesta correcta para ambos.

    El borrado es definitivo. No hay baja logica aqui: a diferencia de los
    tipos de pago, no hay historial financiero que proteger.
    """
    with get_cursor(commit=True) as cursor:
        if not repositorio.eliminar_columna(cursor, curso_id, columna_id):
            raise ColumnaNoEncontradaError(COLUMNA_NO_ENCONTRADA)


def _validar_pertenencia(marcas, columnas_del_curso, estudiantes_del_curso):
    """Que cada celda sea de este curso. Se comprueba **el lote entero** antes
    de escribir nada.

    Si se validara celda a celda mientras se guarda, un lote con un error a
    mitad dejaria media pantalla guardada y media no, y el usuario no tendria
    forma de saber cuales. Aqui o entra todo o no entra nada.
    """
    for marca in marcas:
        if marca.columna_id not in columnas_del_curso:
            raise MarcasFueraDelCursoError(MARCAS_FUERA_DEL_CURSO)
        if marca.estudiante_id not in estudiantes_del_curso:
            raise MarcasFueraDelCursoError(MARCAS_FUERA_DEL_CURSO)


def guardar_marcas_controller(curso_id, marcas):
    """Guarda el lote entero. Devuelve cuantas celdas quedaron escritas.

    Un curso inexistente no se comprueba aparte: sin columnas ni alumnos, la
    primera celda del lote ya queda fuera del curso y sale el 422 que el
    documento pide para este endpoint. Ahorra una consulta y no inventa una
    respuesta que el documento no define.

    Que el lote no venga vacio y no traiga celdas repetidas lo garantiza
    `LoteDeMarcas` antes de llegar aqui. Lo segundo no es un capricho: el
    repositorio escribe todo en una sentencia con `ON CONFLICT`, y PostgreSQL
    la aborta entera si la misma celda aparece dos veces.

    Leer, validar y escribir ocurren en la misma transaccion, asi que nadie
    puede borrar entre medias una columna que se acaba de dar por buena.
    """
    with get_cursor(commit=True) as cursor:
        columnas_del_curso = {
            columna_id
            for columna_id, _ in repositorio.leer_columnas_del_curso(cursor, curso_id)
        }
        estudiantes_del_curso = {
            estudiante_id
            for estudiante_id, _, _ in repositorio.leer_estudiantes_del_curso(
                cursor, curso_id
            )
        }

        _validar_pertenencia(marcas, columnas_del_curso, estudiantes_del_curso)

        return repositorio.guardar_marcas(
            cursor,
            [
                (marca.columna_id, marca.estudiante_id, marca.marcado, marca.nota)
                for marca in marcas
            ],
        )
