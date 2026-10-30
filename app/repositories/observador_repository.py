"""Lectura de `observador_anotaciones`, la bitacora del observador.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Como los demas
repositorios, recibe el cursor que ya abrio quien llama y no abre, cierra,
confirma ni revierte nada.

**Una sola consulta, siempre.** Es el motivo de existir de esta funcionalidad:
la pantalla vieja hacia una peticion HTTP por alumno y con 12 tardaba 16-20 s,
por encima del limite de 10 s del frontend. Aqui se abre **un** estudiante y su
bitacora entera sale de una consulta. Contra Neon (`us-east-1`) cada ida y
vuelta cuesta ~180 ms se consulte lo que se consulte, asi que lo que hay que
vigilar es **cuantas** consultas se hacen, no lo complicada que sea cada una.
Si alguien anade aqui una segunda consulta, que sea sabiendo eso.

El nombre del profesor sale de la misma union y no de una consulta aparte. Ese
`JOIN` es interno: `profesor_id` es `NOT NULL` y su clave foranea no lleva
`ON DELETE CASCADE` ni `SET NULL`, asi que PostgreSQL **impide** borrar un
profesor con anotaciones. La fila siempre existe. Dar de baja a un profesor en
esta aplicacion es cambiarle el `estado`, no borrarlo.

La materia es una **etiqueta copiada** en la propia fila, no una union con
`materias`: si manana quitan esa materia del horario, la anotacion conserva el
texto. Tambien ahorra la union.
"""

from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL

# La consulta arranca en `estudiantes`, no en las anotaciones, y eso es lo unico
# que hay que entender de este modulo.
#
# La pantalla necesita el nivel del curso para decidir si muestra la materia
# (preescolar la omite, primaria la lleva en capsula). Si la consulta arrancara
# en `observador_anotaciones`, un alumno **sin anotaciones** devolveria cero
# filas y con ellas ningun nivel: la pantalla no podria ni escribir su titulo.
# Y ese no es un caso raro -hoy es el caso de TODOS los alumnos, porque la
# escritura todavia no existe-.
#
# Arrancando en el estudiante siempre vuelve al menos una fila. Si no tiene
# anotaciones, las columnas de la anotacion llegan en `NULL` y quien llama las
# descarta mirando `id`.
#
# Las dos uniones anadidas son `LEFT` a proposito:
#   - `cursos`, porque `estudiantes.curso_id` es NULABLE. Con un `JOIN` normal,
#     un alumno sin curso desapareceria de su propia bitacora: sin error, sin
#     aviso, simplemente vacia.
#   - `observador_anotaciones`, que es justo lo que permite el caso de arriba.
#
# Ninguna de las dos anade una ida y vuelta: siguen siendo una sola consulta.
#
# Año lectivo (fase 3, paso 3.5b): las anotaciones son las de un año, con el
# filtro tambien en el `ON`, por lo mismo que el del periodo. Sin año, el
# activo y ningun parametro nuevo; el curso del nivel sigue siendo
# `e.curso_id`. Con otro año, el curso de su matricula de ese año.
#
# Firma del acudiente (docs/funcionalidades/FIRMA_OBSERVADOR.md): las
# columnas del final. El director de grupo y el año de cada anotacion sirven
# para decir de antemano si el boton de firmar va a funcionar; la firma, para
# pintar su sello. **La imagen no viaja**: solo su SHA-256, calculado en
# PostgreSQL, que basta para comprobar la huella. Las dos uniones nuevas son
# `LEFT`, van en `_RESTO` y no anaden ninguna ida y vuelta.
_SELECT = """
    SELECT c.nivel,
           a.id,
           a.profesor_id,
           p.nombre,
           p.apellido,
           a.materia,
           a.periodo,
           a.positiva,
           a.conductual,
           a.cognitivo,
           a.lenguaje,
           a.creada_en,
           a.editada_en,
           a.editada_por,
           c.director_grupo_id,
           al.anio,
           al.estado,
           f.firmante_nombre,
           f.firmante_tipo_documento,
           f.firmante_documento,
           f.firmante_parentesco,
           f.tomada_por_profesor_id,
           f.tomada_por_usuario_id,
           f.tomada_por_nombre,
           f.firmada_en,
           f.huella,
           encode(sha256(f.imagen_png), 'hex')
    FROM estudiantes e
    LEFT JOIN cursos c ON c.id = {curso}
    LEFT JOIN observador_anotaciones a
           ON a.estudiante_id = e.id
          AND a.anio_lectivo_id = {anio}
"""


def _select_del_anio(anio_lectivo_id):
    """`_SELECT` con su año, y los parametros que agrega (van primero)."""
    if anio_lectivo_id is None:
        return _SELECT.format(curso="e.curso_id", anio=ANIO_ACTIVO_ID_SQL), ()
    curso = (
        "(SELECT m.curso_id FROM matriculas m"
        " WHERE m.estudiante_id = e.id AND m.anio_lectivo_id = %s)"
    )
    return _SELECT.format(curso=curso, anio="%s"), (anio_lectivo_id, anio_lectivo_id)


# El filtro de periodo va en el ON de la union, NO en el WHERE. En el WHERE
# descartaria tambien la fila del estudiante cuando ese periodo no tuviera
# anotaciones, y volveriamos a quedarnos sin nivel.
_FILTRO_PERIODO = "          AND a.periodo = %s\n"

_RESTO = """
    LEFT JOIN profesor p ON p.id = a.profesor_id
    LEFT JOIN anios_lectivos al ON al.id = a.anio_lectivo_id
    LEFT JOIN observador_firmas f ON f.anotacion_id = a.id
    WHERE e.id = %s
    ORDER BY a.creada_en DESC NULLS LAST, a.id DESC NULLS LAST
"""


def leer_bitacora(cursor, estudiante_id, periodo=None, anio_lectivo_id=None):
    """El nivel del curso del estudiante y todas sus anotaciones.

    Devuelve las filas crudas. Quien llama distingue las anotaciones reales de
    la fila de relleno mirando si el `id` -la segunda columna- es `None`, y
    saca el nivel de la primera columna de cualquier fila.

    Devuelve **lista vacia solo si el estudiante no existe**. Un alumno real sin
    anotaciones devuelve exactamente una fila, con el nivel y el resto en
    `NULL`. Esa diferencia es la que deja distinguir «no existe» de «todavia no
    tiene nada escrito», que en pantalla son mensajes distintos.

    `periodo` es **opcional a proposito**: sin el devuelve el ano entero. El
    periodo es una etiqueta de cada anotacion, no un filtro obligatorio, y
    cambiar de periodo en la pantalla nunca puede ocultar historial. Es el
    invariante 5 del documento.

    El desempate por `id DESC` no es adorno: dos anotaciones guardadas en la
    misma transaccion comparten `creada_en` al milisegundo, porque `now()` es el
    instante de la transaccion y no el de la fila. Sin el, su orden entre si
    quedaria a criterio de PostgreSQL y podria cambiar entre dos lecturas
    identicas.

    Las anotaciones son las de un año (fase 3 del año lectivo): sin
    `anio_lectivo_id`, el activo, que es lo unico que ve un profesor
    (decision 4).
    """
    select, params_anio = _select_del_anio(anio_lectivo_id)
    if periodo is None:
        cursor.execute(select + _RESTO, (*params_anio, estudiante_id))
    else:
        cursor.execute(
            select + _FILTRO_PERIODO + _RESTO,
            (*params_anio, periodo, estudiante_id),
        )
    return cursor.fetchall()


# Los alumnos de un profesor: los de TODOS los cursos donde tiene clase.
#
# Es **el mismo JOIN** que `_SQL_PROFESOR_COMPARTE_CURSO` de
# `app/core/permissions.py`, el que decide si un profesor puede abrir la
# bitacora de un nino. Que sean la misma regla no es casualidad ni ahorro: si
# esta consulta fuera mas ancha, la pantalla listaria alumnos que al abrirlos
# darian 403; si fuera mas estrecha, esconderia alumnos que si puede ver. Quien
# toque una de las dos tiene que mirar la otra.
#
# **El `DISTINCT` no es cosmetico.** Un profesor puede tener varias asignaciones
# en el mismo curso -medido: el 73% de los pares profesor-curso dan mas de una
# materia, y una profesora da 9 en PRIMERO-A-, asi que sin el cada alumno
# saldria repetido una vez por materia.
#
# Un alumno sin curso (`estudiantes.curso_id` es nulable) no aparece, porque el
# JOIN no encuentra pareja. Es exactamente lo que hace el guard: nadie puede
# abrir su bitacora por esta puerta, asi que listarlo seria mentir.
_SELECT_MIS_ESTUDIANTES = """
    SELECT DISTINCT e.id, e.nombre, e.apellido, e.curso_id, c.nombre
    FROM estudiantes e
    JOIN asignaciones a ON a.curso_id = e.curso_id
    LEFT JOIN cursos c ON c.id = e.curso_id
    WHERE a.profesor_id = %s
      AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
    ORDER BY c.nombre, e.apellido, e.nombre
"""


def leer_estudiantes_del_profesor(cursor, profesor_id):
    """Todos los alumnos del profesor, ordenados por curso y apellido.

    **Una sola consulta.** La alternativa era pedir sus clases y despues los
    alumnos de cada una: con 6 cursos serian 7 idas y vueltas, y contra Neon
    cada una cuesta ~180 ms. Seria reconstruir el N+1 que esta funcionalidad
    vino a matar, en la pantalla que existe para matarlo.

    Medido contra la base real antes de escribirla: el peor caso son 81 alumnos
    -un profesor con 6 cursos- y la consulta tarda 69 ms, menos que una ida y
    vuelta. Lo que se paga es el viaje, no la consulta.

    Solo alumnos **activos**, igual que `GET /planilla/{asignacion_id}`, que es
    la lista que esta reemplazando. La bitacora de un alumno retirado se sigue
    pudiendo leer si se llega a ella por su id: esto filtra la lista, no el
    permiso.
    """
    cursor.execute(_SELECT_MIS_ESTUDIANTES, (profesor_id,))
    return cursor.fetchall()


def crear_anotacion(
    cursor,
    estudiante_id,
    profesor_id,
    periodo,
    conductual,
    cognitivo,
    lenguaje,
):
    """Inserta una anotacion nueva y devuelve su id.

    `profesor_id` lo pone quien llama a partir del token, **nunca** del cuerpo
    de la peticion: es el invariante 4 del documento.

    `materia` no se toca: se queda en su valor por defecto, la cadena vacia. Por
    ahora no se rellena, y el motivo esta en el documento.

    `positiva` tampoco se toca desde el 2026-09-09, cuando el usuario quito la
    marca de buena o mala: la fila nace con `NULL`. La columna se conserva -no se
    borra nada- por si algun dia vuelve.

    El `commit` es de quien llama, como en los demas repositorios.
    """
    # Fase 1 del año lectivo: la anotacion nace en el año activo.
    cursor.execute(
        f"""
        INSERT INTO observador_anotaciones (
            estudiante_id, profesor_id, periodo,
            conductual, cognitivo, lenguaje, anio_lectivo_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, {ANIO_ACTIVO_ID_SQL})
        RETURNING id
        """,
        (estudiante_id, profesor_id, periodo, conductual, cognitivo, lenguaje),
    )
    return cursor.fetchone()[0]


def actualizar_anotacion_del_autor(
    cursor,
    anotacion_id,
    profesor_id,
    conductual,
    cognitivo,
    lenguaje,
):
    """Actualiza la anotacion **solo si la escribio ese profesor**.

    Devuelve `True` si actualizo, `False` si no habia ninguna fila que
    cumpliera las dos condiciones. Quien llama distingue entonces «no existe»
    de «no es tuya» con una segunda consulta, que solo se paga en el camino de
    error.

    El `profesor_id` va en el `WHERE`, no en un `if` previo: asi la comprobacion
    de autoria y la escritura son **la misma sentencia**, y no hay ventana entre
    comprobar y escribir. Es tambien el invariante 3 -el admin no edita
    anotaciones de profesores-, porque el id de un admin sale de `usuarios` y
    nunca coincidira con el autor... salvo por casualidad numerica, que es justo
    lo que el guard de la ruta impide antes de llegar aqui.

    Editar **siempre deja rastro**: `editada_en` y `editada_por` se fijan en la
    misma sentencia, sin depender de que quien llame se acuerde. Es el
    invariante 2.

    **No toca `positiva`** desde el 2026-09-09. Antes la sobrescribia en cada
    edicion, asi que corregir una heredada obligaba a ponerle una marca que no
    tenia. Ahora una fila conserva la que tuviera, y las nuevas nacen sin
    ninguna.
    """
    cursor.execute(
        """
        UPDATE observador_anotaciones
           SET conductual = %s,
               cognitivo = %s,
               lenguaje = %s,
               editada_en = now(),
               editada_por = %s
         WHERE id = %s AND profesor_id = %s
        RETURNING id
        """,
        (conductual, cognitivo, lenguaje, profesor_id, anotacion_id, profesor_id),
    )
    return cursor.fetchone() is not None


def leer_autor(cursor, anotacion_id):
    """El `profesor_id` que escribio la anotacion, o `None` si no existe.

    **Solo se usa en el camino de error de la edicion**, para distinguir un 404
    de un 403. En el camino normal no se ejecuta, asi que guardar sigue
    costando una sola ida y vuelta.
    """
    cursor.execute(
        "SELECT profesor_id FROM observador_anotaciones WHERE id = %s",
        (anotacion_id,),
    )
    fila = cursor.fetchone()
    return fila[0] if fila else None


# ---------------------------------------------------------------------------
# Firma del acudiente. Ver docs/funcionalidades/FIRMA_OBSERVADOR.md.
# ---------------------------------------------------------------------------

# `FOR UPDATE OF a` bloquea **solo la fila de la anotacion** hasta el fin de la
# transaccion (con uniones izquierdas, PostgreSQL exige decir cual). Es lo que
# impide firmar un texto que otro esta editando: la edicion pide el mismo
# bloqueo antes de escribir (`bloquear_y_saber_si_esta_firmada`), asi que una
# de las dos espera a la otra. Si gana la edicion, esta lectura devuelve el
# texto nuevo y la version ya no coincide; si gana la firma, la edicion ve la
# firma y se rechaza.
#
# El director de grupo es el del curso **actual** del alumno: un profesor solo
# firma en el año activo (la misma regla de año que editar), y para el admin,
# el unico que firma en otros años, no hace falta.
#
# El nombre de quien toma la firma sale de su tabla -`profesor` o `usuarios`,
# segun el rol- con una subconsulta, para no pagar otra ida y vuelta. `now()`
# es el instante de la transaccion: la hora que se guarda y la que cubre la
# huella son la misma.
#
# La misma consulta sirve para una anotacion o para varias (la firma de un
# periodo): cambia solo el `WHERE`. Con varias, el `ORDER BY a.id` bloquea las
# filas siempre en el mismo orden, para que dos firmas simultaneas no se
# esperen la una a la otra en orden cruzado.
_SQL_PARA_FIRMAR = """
    SELECT a.id,
           a.estudiante_id,
           a.profesor_id,
           a.periodo,
           a.conductual,
           a.cognitivo,
           a.lenguaje,
           a.creada_en,
           a.editada_en,
           al.anio,
           al.estado,
           c.director_grupo_id,
           f.id IS NOT NULL,
           (SELECT concat_ws(' ', NULLIF(p.nombre, ''), NULLIF(p.apellido, ''))
              FROM profesor p
             WHERE p.id = %s),
           (SELECT u.nombre FROM usuarios u WHERE u.id = %s),
           now()
    FROM observador_anotaciones a
    JOIN estudiantes e ON e.id = a.estudiante_id
    LEFT JOIN cursos c ON c.id = e.curso_id
    LEFT JOIN anios_lectivos al ON al.id = a.anio_lectivo_id
    LEFT JOIN observador_firmas f ON f.anotacion_id = a.id
    {donde}
    FOR UPDATE OF a
"""
_SQL_ANOTACION_PARA_FIRMAR = _SQL_PARA_FIRMAR.format(donde="WHERE a.id = %s")
_SQL_ANOTACIONES_PARA_FIRMAR = _SQL_PARA_FIRMAR.format(
    donde="WHERE a.id = ANY(%s)\n    ORDER BY a.id"
)


def _anotacion_para_firmar(fila):
    """Una fila de `_SQL_PARA_FIRMAR`, con la forma que usa la ruta."""
    (
        anotacion_id,
        estudiante_id,
        autor_id,
        periodo,
        conductual,
        cognitivo,
        lenguaje,
        creada_en,
        editada_en,
        anio,
        estado,
        director_grupo_id,
        firmada,
        nombre_profesor,
        nombre_usuario,
        ahora,
    ) = fila

    return {
        "anotacion": {
            "id": anotacion_id,
            "estudiante_id": estudiante_id,
            "profesor_id": autor_id,
            "periodo": periodo,
            "conductual": conductual,
            "cognitivo": cognitivo,
            "lenguaje": lenguaje,
            "creada_en": creada_en,
            "editada_en": editada_en,
        },
        "anio_y_estado": (anio, estado) if anio is not None else None,
        "director_grupo_id": director_grupo_id,
        "firmada": bool(firmada),
        # `concat_ws` devuelve '' y no NULL cuando faltan nombre y apellido.
        "tomada_por_nombre": nombre_profesor or nombre_usuario or "",
        "ahora": ahora,
    }


def leer_anotacion_para_firmar(cursor, anotacion_id, profesor_id=None, usuario_id=None):
    """Todo lo necesario para firmar una anotacion, con su fila bloqueada.

    Una sola consulta. Devuelve `None` si la anotacion no existe; si no, un
    diccionario con:

    - `anotacion`: el contenido que cubren la version y la huella;
    - `anio_y_estado`: `(anio, estado)` para la guardia del año;
    - `director_grupo_id`: el del curso actual del alumno;
    - `firmada`: si ya tiene firma;
    - `tomada_por_nombre`: el nombre de quien la toma (profesor o admin);
    - `ahora`: el instante de la transaccion.

    `profesor_id` o `usuario_id`, segun el rol de quien firma; el otro va en
    `None`. Salen del token, nunca del cuerpo.
    """
    cursor.execute(_SQL_ANOTACION_PARA_FIRMAR, (profesor_id, usuario_id, anotacion_id))
    fila = cursor.fetchone()
    return _anotacion_para_firmar(fila) if fila is not None else None


def leer_anotaciones_para_firmar(cursor, anotacion_ids, profesor_id=None, usuario_id=None):
    """Lo mismo que `leer_anotacion_para_firmar`, para varias: la firma de un
    periodo. Una sola consulta, con todas las filas bloqueadas.

    Devuelve solo las que existen, ordenadas por id. Si falta alguna, quien
    llama lo nota porque devuelve menos de las que pidio.
    """
    cursor.execute(
        _SQL_ANOTACIONES_PARA_FIRMAR,
        (profesor_id, usuario_id, list(anotacion_ids)),
    )
    return [_anotacion_para_firmar(fila) for fila in cursor.fetchall()]


def crear_firma(cursor, anotacion_id, firma, imagen, huella):
    """Inserta la firma y devuelve su id. El `commit` es de quien llama.

    Si otra firma de la misma anotacion se guardo mientras tanto, el UNIQUE de
    `anotacion_id` la rechaza con `UniqueViolation`, y la ruta lo traduce a un
    409. Es la ultima defensa del invariante 1.
    """
    cursor.execute(
        """
        INSERT INTO observador_firmas (
            anotacion_id,
            firmante_nombre,
            firmante_tipo_documento,
            firmante_documento,
            firmante_parentesco,
            imagen_png,
            tomada_por_profesor_id,
            tomada_por_usuario_id,
            tomada_por_nombre,
            firmada_en,
            huella
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            anotacion_id,
            firma["firmante_nombre"],
            firma["firmante_tipo_documento"],
            firma["firmante_documento"],
            firma["firmante_parentesco"],
            imagen,
            firma["tomada_por_profesor_id"],
            firma["tomada_por_usuario_id"],
            firma["tomada_por_nombre"],
            firma["firmada_en"],
            huella,
        ),
    )
    return cursor.fetchone()[0]


_COLUMNAS_DE_LA_FIRMA = """
            anotacion_id,
            firmante_nombre,
            firmante_tipo_documento,
            firmante_documento,
            firmante_parentesco,
            imagen_png,
            tomada_por_profesor_id,
            tomada_por_usuario_id,
            tomada_por_nombre,
            firmada_en,
            huella
"""


def crear_firmas(cursor, firma, imagen, huellas):
    """Inserta la misma firma en varias anotaciones: la firma de un periodo.

    `huellas` son pares `(anotacion_id, huella)`: todo lo demas -quien firmo,
    la imagen, quien la tomo y la hora- es igual en todas las filas, pero cada
    huella cubre el texto de su anotacion. **Un solo `INSERT`** con una fila
    por anotacion: contra Neon, una ida y vuelta por anotacion seria pagar
    ~180 ms por cada una. Devuelve los pares `(id, anotacion_id)` creados.

    Va en la misma transaccion que la lectura bloqueada: o se firman todas o
    ninguna. Si otra firma de alguna se guardo mientras tanto, el UNIQUE de
    `anotacion_id` rechaza el `INSERT` entero.
    """
    # Solo se repiten marcadores `%s`, nunca datos: el SQL no lleva nada que
    # venga de fuera.
    filas = ", ".join(["(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"] * len(huellas))
    parametros = []
    for anotacion_id, huella in huellas:
        parametros.extend(
            [
                anotacion_id,
                firma["firmante_nombre"],
                firma["firmante_tipo_documento"],
                firma["firmante_documento"],
                firma["firmante_parentesco"],
                imagen,
                firma["tomada_por_profesor_id"],
                firma["tomada_por_usuario_id"],
                firma["tomada_por_nombre"],
                firma["firmada_en"],
                huella,
            ]
        )
    cursor.execute(
        f"INSERT INTO observador_firmas ({_COLUMNAS_DE_LA_FIRMA}) "
        f"VALUES {filas} RETURNING id, anotacion_id",
        parametros,
    )
    return cursor.fetchall()


# Dos sentencias en un solo `execute`: una ida y vuelta, pero **dos
# sentencias, y separadas a proposito**. La primera bloquea la anotacion; si
# una firma la tiene bloqueada, espera a que termine. La segunda empieza
# despues, y en READ COMMITTED cada sentencia mira los datos confirmados en
# ese momento, asi que ve la firma recien guardada. Juntas en una sola
# sentencia (un `JOIN` o un `NOT EXISTS` en el `UPDATE`) no servirian:
# despues de esperar, PostgreSQL relee la fila bloqueada pero no la otra
# tabla, y la edicion pisaria un texto ya firmado.
_SQL_BLOQUEAR_Y_VER_FIRMA = """
    SELECT 1 FROM observador_anotaciones WHERE id = %s FOR UPDATE;
    SELECT EXISTS (SELECT 1 FROM observador_firmas WHERE anotacion_id = %s)
"""


def bloquear_y_saber_si_esta_firmada(cursor, anotacion_id):
    """Bloquea la anotacion para editarla y dice si ya tiene firma.

    Con `psycopg2`, de varias sentencias en un `execute` solo queda el
    resultado de la ultima: el `EXISTS`. Si la anotacion no existe, devuelve
    `False` y la edicion sigue su camino de siempre, que responde 404.
    """
    cursor.execute(_SQL_BLOQUEAR_Y_VER_FIRMA, (anotacion_id, anotacion_id))
    fila = cursor.fetchone()
    return bool(fila and fila[0])


# Las mismas anotaciones que `leer_bitacora` para el mismo año y periodo -se
# imprime lo que se ve-, pero solo las firmadas y **con su imagen**. Esta es la
# unica consulta que trae imagenes, y solo se paga al imprimir.
_SELECT_FIRMAS = """
    SELECT a.id,
           a.estudiante_id,
           a.profesor_id,
           a.periodo,
           a.conductual,
           a.cognitivo,
           a.lenguaje,
           a.creada_en,
           a.editada_en,
           f.firmante_nombre,
           f.firmante_tipo_documento,
           f.firmante_documento,
           f.firmante_parentesco,
           f.tomada_por_profesor_id,
           f.tomada_por_usuario_id,
           f.tomada_por_nombre,
           f.firmada_en,
           f.huella,
           f.imagen_png
    FROM observador_anotaciones a
    JOIN observador_firmas f ON f.anotacion_id = a.id
    WHERE a.estudiante_id = %s
      AND a.anio_lectivo_id = {anio}
"""


def leer_firmas_para_imprimir(cursor, estudiante_id, periodo=None, anio_lectivo_id=None):
    """Las firmas, con imagen, de las anotaciones de un alumno. Una consulta.

    Sin `anio_lectivo_id`, las del año activo, como la bitacora.
    """
    if anio_lectivo_id is None:
        sql = _SELECT_FIRMAS.format(anio=ANIO_ACTIVO_ID_SQL)
        params = (estudiante_id,)
    else:
        sql = _SELECT_FIRMAS.format(anio="%s")
        params = (estudiante_id, anio_lectivo_id)
    if periodo is not None:
        sql += "      AND a.periodo = %s\n"
        params += (periodo,)
    cursor.execute(sql + "    ORDER BY a.creada_en DESC, a.id DESC\n", params)
    return cursor.fetchall()


def leer_firmantes_sugeridos(cursor, estudiante_id, profesor_id=None):
    """El padre y la madre de la ficha, y si ese profesor puede pedirlos.

    Devuelve `(nombre_padre, tipo_documento_padre, documento_padre,
    nombre_madre, tipo_documento_madre, documento_madre, puede)`, o `None` si
    el estudiante no existe. Una consulta.

    `puede` responde a "¿este profesor podria tomar alguna firma de este
    alumno?": es su director de grupo o escribio alguna anotacion suya este
    año. Los documentos de los padres son para quien va a tomar una firma, no
    para todos los profesores que comparten curso. Con `profesor_id` nulo (el
    admin) sale falso, y la ruta no lo mira.
    """
    cursor.execute(
        f"""
        SELECT e.nombre_padre,
               e.tipo_documento_padre,
               e.documento_padre,
               e.nombre_madre,
               e.tipo_documento_madre,
               e.documento_madre,
               COALESCE(c.director_grupo_id = %s, false)
               OR EXISTS (
                   SELECT 1
                   FROM observador_anotaciones a
                   WHERE a.estudiante_id = e.id
                     AND a.profesor_id = %s
                     AND a.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
               )
        FROM estudiantes e
        LEFT JOIN cursos c ON c.id = e.curso_id
        WHERE e.id = %s
        """,
        (profesor_id, profesor_id, estudiante_id),
    )
    return cursor.fetchone()
