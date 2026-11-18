"""Acceso a datos de las firmas guardadas para el boletin.

Ver `docs/funcionalidades/FIRMAS_BOLETIN.md`. Funciones puras de datos: reciben
el cursor y devuelven filas; no abren, confirman ni cierran nada.

Las tablas (`firma_institucional`, `firmas_profesores`) solo se leen aqui. La
imagen nunca se une a otra consulta: sale por las rutas de `/firmas`, que
exigen el rol, y por el boletin del admin.
"""
from app.repositories.boletin_repository import _curso_del_estudiante


# --------------------------------------------------------------------------
# Firma del rector(a): una sola fila, id = 1
# --------------------------------------------------------------------------

def leer_firma_institucional(cursor):
    """(imagen_png, actualizado_en), o `None` si no hay firma guardada."""
    cursor.execute(
        """
        SELECT imagen_png, actualizado_en
        FROM firma_institucional
        WHERE id = 1
        """
    )
    return cursor.fetchone()


def guardar_firma_institucional(cursor, imagen_png, usuario_id):
    """Guarda o reemplaza la firma. Devuelve (actualizado_en,)."""
    cursor.execute(
        """
        INSERT INTO firma_institucional (id, imagen_png, actualizado_en, actualizado_por_id)
        VALUES (1, %s, CURRENT_TIMESTAMP, %s)
        ON CONFLICT (id) DO UPDATE
        SET imagen_png = EXCLUDED.imagen_png,
            actualizado_en = EXCLUDED.actualizado_en,
            actualizado_por_id = EXCLUDED.actualizado_por_id
        RETURNING actualizado_en
        """,
        (imagen_png, usuario_id),
    )
    return cursor.fetchone()


def borrar_firma_institucional(cursor):
    cursor.execute("DELETE FROM firma_institucional WHERE id = 1")


# --------------------------------------------------------------------------
# Firma de cada profesor
# --------------------------------------------------------------------------

def leer_firma_de_profesor(cursor, profesor_id):
    """(imagen_png, actualizado_en), o `None` si no hay firma guardada."""
    cursor.execute(
        """
        SELECT imagen_png, actualizado_en
        FROM firmas_profesores
        WHERE profesor_id = %s
        """,
        (profesor_id,),
    )
    return cursor.fetchone()


def guardar_firma_de_profesor(cursor, profesor_id, imagen_png):
    """Guarda o reemplaza la firma del profesor. Devuelve (actualizado_en,)."""
    cursor.execute(
        """
        INSERT INTO firmas_profesores (profesor_id, imagen_png, actualizado_en)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (profesor_id) DO UPDATE
        SET imagen_png = EXCLUDED.imagen_png,
            actualizado_en = EXCLUDED.actualizado_en
        RETURNING actualizado_en
        """,
        (profesor_id, imagen_png),
    )
    return cursor.fetchone()


def borrar_firma_de_profesor(cursor, profesor_id):
    cursor.execute("DELETE FROM firmas_profesores WHERE profesor_id = %s", (profesor_id,))


# --------------------------------------------------------------------------
# Boletin del admin
# --------------------------------------------------------------------------

def leer_firmas_del_boletin(cursor, director_grupo_id):
    """Las dos firmas del boletin en una sola consulta: la del rector(a) y la
    del director de grupo del curso. Cada una puede venir en `None`; sin
    director (`director_grupo_id` en `None`) la segunda siempre lo es.
    """
    cursor.execute(
        """
        SELECT
            (SELECT imagen_png FROM firma_institucional WHERE id = 1)
                AS firma_institucional,
            (SELECT imagen_png FROM firmas_profesores WHERE profesor_id = %s)
                AS firma_director_grupo
        """,
        (director_grupo_id,),
    )
    return cursor.fetchone()


# --------------------------------------------------------------------------
# Observador que imprime el admin (2026-11-18)
# --------------------------------------------------------------------------

def leer_firma_del_director_de_grupo(cursor, estudiante_id, anio_lectivo_id=None):
    """El director de grupo del curso del estudiante y su firma guardada, en una
    consulta: `(nombre, apellido, imagen_png, actualizado_en)`.

    El curso es el mismo que usa el boletin: sin año, el de hoy
    (`e.curso_id`); con año, el de su matricula de ese año. `None` si el
    estudiante no existe. Sin director, o sin firma guardada, esas columnas
    vienen en `None`.
    """
    curso, params_curso = _curso_del_estudiante(anio_lectivo_id)
    cursor.execute(
        f"""
        SELECT dg.nombre, dg.apellido, fp.imagen_png, fp.actualizado_en
        FROM estudiantes e
        LEFT JOIN cursos c ON {curso} = c.id
        LEFT JOIN profesor dg ON dg.id = c.director_grupo_id
        LEFT JOIN firmas_profesores fp ON fp.profesor_id = dg.id
        WHERE e.id = %s
        """,
        (*params_curso, estudiante_id),
    )
    return cursor.fetchone()
