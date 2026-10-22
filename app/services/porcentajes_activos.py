"""Que clases tienen sus porcentajes por tipo de nota activos.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md` (parte B, QB2). Lo usan todas
las lecturas y escrituras que cambian con porcentajes activos: el boletin
(guardar y leer), el boletin del admin, el reporte parcial y los rankings. Asi
la regla "todo o nada" se aplica igual en todos lados.

Lee con el cursor que le pasan y no abre, confirma ni cierra nada. La regla en
si vive en `app/core/nota_periodo.py`.
"""
from app.core.nota_periodo import porcentajes_activos
from app.repositories import porcentajes_planilla_repository as repositorio


def porcentajes_activos_de(cursor, asignacion_id, periodo):
    """Los porcentajes de una clase si estan activos; si no, None.

    Una consulta si la clase no tiene ninguno; dos si los tiene.
    """
    porcentajes = dict(repositorio.leer_porcentajes_de_planilla(cursor, asignacion_id, periodo))
    if not porcentajes:
        return None
    tipos = repositorio.leer_tipos_de_planilla(cursor, asignacion_id, periodo)
    return porcentajes if porcentajes_activos(tipos, porcentajes) else None


def porcentajes_activos_de_asignaciones(cursor, asignacion_ids, periodo):
    """`{asignacion_id: porcentajes}` de las clases con porcentajes activos.

    Sin clases no consulta nada; si ninguna tiene porcentajes, una consulta;
    si alguna los tiene, dos. **No crece con el numero de clases.**
    """
    if not asignacion_ids:
        return {}
    por_clase = {}
    for asignacion_id, tipo_nota, porcentaje in repositorio.leer_porcentajes_de_asignaciones(
        cursor, list(asignacion_ids), periodo
    ):
        por_clase.setdefault(asignacion_id, {})[tipo_nota] = porcentaje
    if not por_clase:
        return {}

    tipos = {}
    for asignacion_id, descripcion in repositorio.leer_tipos_de_asignaciones(
        cursor, list(por_clase), periodo
    ):
        tipos.setdefault(asignacion_id, []).append(descripcion)

    return {
        asignacion_id: porcentajes
        for asignacion_id, porcentajes in por_clase.items()
        if porcentajes_activos(tipos.get(asignacion_id, []), porcentajes)
    }
