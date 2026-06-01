from fastapi import APIRouter, Depends

from app.core.tenant_status import build_tenant_status_response, get_tenant_by_schema
from app.dependencies import get_current_user

router = APIRouter(tags=["Tenant"])


@router.get("/tenant/status")
def tenant_status(current_user: dict = Depends(get_current_user)):
    tenant = get_tenant_by_schema(current_user["tenant"])
    return build_tenant_status_response(tenant or {"estado": "suspendido"})
