from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.controllers.super_admin_controller import (
    actualizar_estado_tenant_controller,
    listar_auditoria_tenant_controller,
    listar_tenants_controller,
)
from app.core.super_admin import get_current_super_admin

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])


class TenantEstadoUpdate(BaseModel):
    estado: str
    motivo: str | None = None


@router.get("/tenants")
def listar_tenants(_super_admin: dict = Depends(get_current_super_admin)):
    return listar_tenants_controller()


@router.patch("/tenants/{tenant_id}/estado")
def actualizar_estado_tenant(
    tenant_id: int,
    data: TenantEstadoUpdate,
    super_admin: dict = Depends(get_current_super_admin),
):
    return actualizar_estado_tenant_controller(
        tenant_id,
        data.estado,
        super_admin["id"],
        data.motivo,
    )


@router.get("/tenants/{tenant_id}/estado-auditoria")
def listar_auditoria_tenant(
    tenant_id: int,
    _super_admin: dict = Depends(get_current_super_admin),
):
    return listar_auditoria_tenant_controller(tenant_id)
