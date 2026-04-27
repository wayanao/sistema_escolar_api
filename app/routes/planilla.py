from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.planilla import NotaPlanillaCreate
from app.controllers.planilla_controller import registrar_nota_planilla_controller
from app.controllers.planilla_controller import eliminar_tipo_controller

router = APIRouter(tags=["Planilla"], dependencies=[Depends(get_current_user)])


# 📝 Registrar nota desde planilla
@router.post("/planilla/nota")
def registrar_nota(data: NotaPlanillaCreate):

    return registrar_nota_planilla_controller(data)
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.controllers.planilla_excel_controller import planilla_excel_controller

# 📊 Descargar planilla en formato Excel
@router.get("/planilla-excel/{asignacion_id}/{periodo}")
def planilla_excel(asignacion_id: int, periodo: int = 1):
    return planilla_excel_controller(asignacion_id, periodo)

# 🗑️ Eliminar tipo de nota desde planilla
@router.delete("/planilla/tipo")
def eliminar_tipo(asignacion_id: int, descripcion: str, periodo: int = 1):
    return eliminar_tipo_controller(asignacion_id, descripcion, periodo)