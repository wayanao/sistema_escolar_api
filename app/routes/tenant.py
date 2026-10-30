from fastapi import APIRouter, Depends

from app.core.tenant_status import (
    build_tenant_status_response,
    colegio_usa_entrevista_admision,
    get_tenant_by_schema,
)
from app.dependencies import get_current_user

router = APIRouter(tags=["Tenant"])


@router.get("/tenant/status")
def tenant_status(current_user: dict = Depends(get_current_user)):
    tenant = get_tenant_by_schema(current_user["tenant"])
    respuesta = build_tenant_status_response(tenant or {"estado": "suspendido"})
    # 2026-10-30: el frontend decide con esto qué mostrar de Admisiones y de
    # "Crear estudiante" en el año en preparación. Quien lo hace cumplir es el
    # backend (`exigir_entrevista_admision` y el alta directa).
    respuesta["usa_entrevista_admision"] = colegio_usa_entrevista_admision(
        current_user["tenant"]
    )
    return respuesta
