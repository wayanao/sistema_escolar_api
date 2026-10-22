from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.core.permissions import require_asignacion_access
from app.controllers.planilla_excel_controller import planilla_excel_controller
from app.schemas.planilla import NotaPlanillaCreate
from app.controllers.planilla_controller import NotaCalculadaError
from app.controllers.planilla_controller import registrar_nota_planilla_controller
from app.controllers.planilla_controller import eliminar_tipo_controller

router = APIRouter(tags=["Planilla"], dependencies=[Depends(get_current_user)])


# 📝 Registrar nota desde planilla
@router.post("/planilla/nota")
def registrar_nota(data: NotaPlanillaCreate, current_user: dict = Depends(get_current_user)):
    require_asignacion_access(data.asignacion_id, current_user)

    try:
        return registrar_nota_planilla_controller(data, usuario=current_user)
    except NotaCalculadaError as exc:
        # Subnotas, paso A1: la celda tiene subnotas calificadas (P1).
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

# 📊 Descargar planilla en formato Excel
@router.get("/planilla-excel/{asignacion_id}/{periodo}")
def planilla_excel(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user),
    con_subnotas: bool = False,
    con_porcentajes: bool = False,
):
    require_asignacion_access(asignacion_id, current_user)
    # Subnotas (paso A1) y porcentajes (paso B2b): sin los parametros, la misma
    # llamada y la misma respuesta de siempre (Asistencia usa esta ruta solo
    # para la lista). Cada uno pide solo lo suyo.
    opciones = {}
    if con_subnotas:
        opciones["con_subnotas"] = True
    if con_porcentajes:
        opciones["con_porcentajes"] = True
    return planilla_excel_controller(asignacion_id, periodo, **opciones)

# 🗑️ Eliminar tipo de nota desde planilla
@router.delete("/planilla/tipo")
def eliminar_tipo(
    asignacion_id: int,
    descripcion: str,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user)
):
    require_asignacion_access(asignacion_id, current_user)
    return eliminar_tipo_controller(asignacion_id, descripcion, periodo, usuario=current_user)
