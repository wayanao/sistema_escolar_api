"""«Mi curso» del director de grupo: los cursos que dirige y el ranking de uno.

Ver `docs/funcionalidades/MI_CURSO_DIRECTOR.md`. El permiso (director del curso
o admin) lo pone la ruta con `require_director_de_curso`; aqui solo se lee y se
arma la respuesta. `armar_mi_curso` es pura: no toca la base.
"""

from decimal import Decimal

from psycopg2.extras import RealDictCursor

from app.core.nivel_academico import (
    NOMBRE_MATERIA_ASISTENCIA_JORNADA,
    resolver_tipo_evaluacion,
)
from app.database import get_cursor
from app.repositories import director_grupo_repository as repositorio


def _numero(valor):
    """`Decimal` de PostgreSQL a `float` con dos decimales; `None` sigue `None`."""
    if valor is None:
        return None
    return round(float(valor), 2) if isinstance(valor, (Decimal, float, int)) else valor


def _nombre_profesor(fila):
    return " ".join(
        parte for parte in (fila.get("profesor_nombre"), fila.get("profesor_apellido")) if parte
    )


def listar_cursos_dirigidos_controller(usuario):
    """Cursos del año activo que dirige el profesor de la sesión.

    El admin no usa esa pantalla: lista vacía, sin consultar la base.
    """
    if usuario.get("rol") != "profesor":
        return []
    with get_cursor(cursor_factory=RealDictCursor) as cursor:
        filas = repositorio.leer_cursos_dirigidos(cursor, usuario.get("id"))
    return [
        {
            "id": fila["id"],
            "nombre": fila["nombre"],
            "jornada": fila.get("jornada"),
            "nivel": fila.get("nivel"),
        }
        for fila in filas
    ]


def obtener_mi_curso_controller(curso_id, periodo):
    """Ranking del curso en el periodo. `None` si el curso no es del año
    activo (la ruta lo vuelve 404)."""
    with get_cursor(cursor_factory=RealDictCursor) as cursor:
        curso = repositorio.leer_curso(cursor, curso_id)
        if not curso:
            return None
        materias = repositorio.leer_materias_del_curso(
            cursor, curso_id, periodo, NOMBRE_MATERIA_ASISTENCIA_JORNADA
        )
        estudiantes = repositorio.leer_estudiantes_con_puesto(cursor, curso_id, periodo)
        asignacion_ids = [fila["asignacion_id"] for fila in materias]
        definitivas = (
            repositorio.leer_definitivas_del_curso(cursor, periodo, asignacion_ids)
            if asignacion_ids
            else []
        )
        inasistencias = repositorio.leer_inasistencias_del_curso(cursor, curso_id, periodo)

    return armar_mi_curso(curso, periodo, materias, estudiantes, definitivas, inasistencias)


def armar_mi_curso(curso, periodo, materias, estudiantes, definitivas, inasistencias):
    """La respuesta de "Mi curso", con las reglas del boletin.

    La definitiva de cada materia es la guardada, o el promedio de la planilla
    si no hay o es 0, como el boletin del admin. `guardada` dice si el profesor
    ya guardo el boletin de ese estudiante: el puesto solo cuenta lo guardado.
    """
    ids_estudiantes = {fila["estudiante_id"] for fila in estudiantes}

    celdas = {}
    for fila in definitivas:
        estudiante_id = fila["estudiante_id"]
        if estudiante_id not in ids_estudiantes:
            continue
        guardada = bool(fila.get("guardada"))
        definitiva_guardada = _numero(fila.get("definitiva_guardada"))
        definitiva = (
            definitiva_guardada
            if guardada and definitiva_guardada not in (None, 0)
            else _numero(fila.get("promedio_planilla"))
        )
        celdas[(estudiante_id, fila["asignacion_id"])] = {
            "definitiva": definitiva,
            "guardada": guardada,
        }

    ausencias = {
        fila["estudiante_id"]: {
            "periodo": int(fila.get("del_periodo") or 0),
            "anio": int(fila.get("del_anio") or 0),
        }
        for fila in inasistencias
    }

    salida_materias = []
    for fila in materias:
        asignacion_id = fila["asignacion_id"]
        guardados = sum(
            1
            for estudiante_id in ids_estudiantes
            if celdas.get((estudiante_id, asignacion_id), {}).get("guardada")
        )
        salida_materias.append({
            "asignacion_id": asignacion_id,
            "materia": fila["materia"],
            "profesor": _nombre_profesor(fila),
            "tipo_evaluacion": resolver_tipo_evaluacion(
                curso.get("nivel"),
                "desarrollo" if fila.get("tiene_desarrollo") else None,
            ),
            "guardados": guardados,
            "total": len(ids_estudiantes),
        })

    sin_nota = {"definitiva": None, "guardada": False}
    salida_estudiantes = [
        {
            "estudiante_id": fila["estudiante_id"],
            "nombre": fila.get("nombre") or "",
            "apellido": fila.get("apellido") or "",
            "puesto": int(fila["puesto"]) if fila.get("puesto") is not None else None,
            "promedio": _numero(fila.get("promedio")),
            "notas": {
                str(materia["asignacion_id"]): celdas.get(
                    (fila["estudiante_id"], materia["asignacion_id"]), dict(sin_nota)
                )
                for materia in materias
            },
            "inasistencias": ausencias.get(fila["estudiante_id"], {"periodo": 0, "anio": 0}),
        }
        for fila in estudiantes
    ]

    total_rankeados = int(estudiantes[0].get("total_rankeados") or 0) if estudiantes else 0

    return {
        "curso": {
            "id": curso["id"],
            "nombre": curso["nombre"],
            "jornada": curso.get("jornada"),
            "nivel": curso.get("nivel"),
        },
        "periodo": periodo,
        "total_rankeados": total_rankeados,
        "materias": salida_materias,
        "estudiantes": salida_estudiantes,
    }
