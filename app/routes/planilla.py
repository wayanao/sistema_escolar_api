from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.database import get_connection
from app.schemas.planilla import NotaPlanillaCreate
from app.controllers.planilla_controller import registrar_nota_planilla_controller
from app.controllers.planilla_controller import eliminar_tipo_controller

router = APIRouter(tags=["Planilla"], dependencies=[Depends(get_current_user)])


def validar_acceso_asignacion(asignacion_id: int, current_user: dict):
    if current_user.get("rol") == "admin":
        return
    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM asignaciones WHERE id = %s AND profesor_id = %s",
            (asignacion_id, current_user.get("id"))
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


# 📝 Registrar nota desde planilla
@router.post("/planilla/nota")
def registrar_nota(data: NotaPlanillaCreate, current_user: dict = Depends(get_current_user)):
    validar_acceso_asignacion(data.asignacion_id, current_user)

    return registrar_nota_planilla_controller(data)
from app.controllers.planilla_excel_controller import planilla_excel_controller

# 📊 Descargar planilla en formato Excel
@router.get("/planilla-excel/{asignacion_id}/{periodo}")
def planilla_excel(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user)
):
    validar_acceso_asignacion(asignacion_id, current_user)
    return planilla_excel_controller(asignacion_id, periodo)

# 🗑️ Eliminar tipo de nota desde planilla
@router.delete("/planilla/tipo")
def eliminar_tipo(
    asignacion_id: int,
    descripcion: str,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user)
):
    validar_acceso_asignacion(asignacion_id, current_user)
    return eliminar_tipo_controller(asignacion_id, descripcion, periodo)
