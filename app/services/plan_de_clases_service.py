from app.repositories.plan_de_clases_repository import (
    actualizar_estado_revision_plan,
    agregar_observacion_plan,
    eliminar_imagen_plan,
    guardar_plan_de_clases,
    listar_observaciones_plan,
    listar_notificaciones_admin,
    listar_notificaciones_profesor,
    listar_planes_admin,
    marcar_observacion_vista,
    obtener_plan_por_id,
    obtener_plan_por_dia,
    obtener_planes_por_asignacion,
)


def guardar_plan(plan, imagen1_path=None, imagen2_path=None, *, usuario):
    resultado = guardar_plan_de_clases(
        plan,
        imagen1_path,
        imagen2_path,
        usuario=usuario,
    )
    if resultado.get("resultado") == "version_desactualizada":
        return resultado

    mensaje = (
        "Plan de clases guardado y enviado a administración"
        if resultado["estado_revision"] == "pendiente"
        else "Cambios guardados; la revisión se conserva"
    )
    return {
        "mensaje": mensaje,
        **resultado,
    }


def obtener_plan_del_dia(asignacion_id, fecha):
    return obtener_plan_por_dia(asignacion_id, fecha)


def obtener_historial_asignacion(asignacion_id, limit=None, offset=0):
    return obtener_planes_por_asignacion(
        asignacion_id,
        limit=limit,
        offset=offset,
    )


def listar_reportes_admin(**filtros):
    return listar_planes_admin(**filtros)


def obtener_plan_admin(plan_id):
    return obtener_plan_por_id(plan_id)


def actualizar_revision(plan_id, estado, admin_id, version, comentario=None):
    return actualizar_estado_revision_plan(
        plan_id,
        estado,
        admin_id,
        version,
        comentario=comentario,
    )


def crear_observacion_plan(plan_id, admin_id, version, observacion):
    return agregar_observacion_plan(plan_id, admin_id, version, observacion)


def obtener_observaciones_plan(plan_id):
    return listar_observaciones_plan(plan_id)


def confirmar_observacion_vista(plan_id, observacion_id, *, usuario):
    return marcar_observacion_vista(plan_id, observacion_id, usuario=usuario)


def obtener_notificaciones_planeadores(current_user, limit=8):
    if current_user.get("rol") == "admin":
        return listar_notificaciones_admin(limit=limit)
    if current_user.get("rol") == "profesor":
        return listar_notificaciones_profesor(current_user["id"], limit=limit)
    return {"total_no_leidas": 0, "items": []}


def eliminar_imagen_plan_admin(plan_id, slot, reiniciar_revision=False, *, usuario):
    return eliminar_imagen_plan(
        plan_id, slot, reiniciar_revision=reiniciar_revision, usuario=usuario
    )
