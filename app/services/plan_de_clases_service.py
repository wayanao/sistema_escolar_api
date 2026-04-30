from app.repositories.plan_de_clases_repository import (
    guardar_plan_de_clases,
    listar_planes_admin,
    obtener_plan_por_dia,
    obtener_planes_por_asignacion,
)


def guardar_plan(plan, imagen1_path=None, imagen2_path=None):
    plan_id = guardar_plan_de_clases(plan, imagen1_path, imagen2_path)
    return {"mensaje": "Plan de clases guardado y enviado a administración", "id": plan_id}


def obtener_plan_del_dia(asignacion_id, fecha):
    return obtener_plan_por_dia(asignacion_id, fecha)


def obtener_historial_asignacion(asignacion_id):
    return obtener_planes_por_asignacion(asignacion_id)


def listar_reportes_admin(**filtros):
    return listar_planes_admin(**filtros)
