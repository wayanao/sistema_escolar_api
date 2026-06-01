import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import jwt, JWTError

from app.config import settings
from app.core.logging import configure_logging
from app.database import close_pool
from app.db.tenant import TENANT_SCHEMA_PATTERN
from app.dependencies import get_current_user
from app.globals import tenant_schema_var
from app.services.storage import (
    normalize_storage_key,
    read_file_bytes,
    remote_file_exists,
    using_remote_storage,
)

from app.routes import (
    asignaciones,
    asistencia,
    auth,
    boletines,
    branding,
    cartera,
    cuentas,
    cursos,
    dashboard,
    egresos,
    estudiantes,
    inventario,
    materias,
    nomina,
    notas,
    observaciones,
    pagos,
    plan_de_clases,
    planeador_anual,
    planilla,
    plantillas,
    prestamos,
    profesores,
    reportes,
    super_admin,
    tenant,
    tipos_pagos,
    usuario,
    ventas,
)

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.ENVIRONMENT)
    yield
    close_pool()
    logger.info("Database pool closed")

# Configuración de Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


UPLOADS_ROOT = Path("uploads").resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validar_acceso_archivo_upload(file_path: str, current_user: dict):
    tenant = current_user["tenant"]
    normalized = normalize_storage_key(file_path)
    candidate = (UPLOADS_ROOT / normalized).resolve()

    if using_remote_storage():
        if not remote_file_exists(normalized):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    elif not _is_relative_to(candidate, UPLOADS_ROOT) or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    parts = Path(normalized).parts
    allowed_file = normalized if using_remote_storage() else candidate

    if len(parts) >= 3 and parts[0] == "branding" and parts[1] == tenant:
        return allowed_file

    if len(parts) >= 3 and parts[0] == tenant and parts[1] == "plan_de_clases":
        if current_user.get("rol") == "admin":
            return allowed_file

        from app.database import get_connection

        stored_path = f"uploads/{normalized}"
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT 1
                FROM plan_de_clases pdc
                JOIN asignaciones a ON a.id = pdc.asignacion_id
                WHERE (pdc.imagen1 = %s OR pdc.imagen2 = %s)
                  AND a.profesor_id = %s
                """,
                (stored_path, stored_path, current_user.get("id")),
            )
            if cursor.fetchone():
                return allowed_file
        finally:
            cursor.close()
            conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


@app.get("/uploads/{file_path:path}")
def servir_upload(file_path: str, current_user: dict = Depends(get_current_user)):
    archivo = _validar_acceso_archivo_upload(file_path, current_user)
    if using_remote_storage():
        stream, content_type = read_file_bytes(str(archivo))
        return StreamingResponse(stream, media_type=content_type or "application/octet-stream")
    return FileResponse(archivo)
# Inicializar limiter en la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 🔥 CORS (SOLO UNA VEZ)
origins = [
    settings.FRONTEND_URL,
]

if settings.ALLOW_DEV_CORS_ORIGINS:
    origins.extend([
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Middleware interceptor para forzar la inyección del contexto (Multi-Tenant) 
# antes de que FastAPI haga su rotación de hilos (threadpooling)
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    tenant_token = tenant_schema_var.set(None)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            tenant = payload.get("tenant")
            if tenant and TENANT_SCHEMA_PATTERN.fullmatch(str(tenant)):
                # Fijamos el contexto a nivel raíz de HTTP
                tenant_schema_var.set(str(tenant))
        except JWTError:
            pass  # Si el token es inválido, lo ignoramos (fastapi/Depends validará y lanzará 401 después)

    try:
        return await call_next(request)
    finally:
        tenant_schema_var.reset(tenant_token)

# 🔗 Rutas
app.include_router(estudiantes.router)
app.include_router(cuentas.router)
app.include_router(pagos.router)
app.include_router(cursos.router)
app.include_router(profesores.router)
app.include_router(asignaciones.router)
app.include_router(notas.router)
app.include_router(planilla.router)
app.include_router(asistencia.router)
app.include_router(auth.router)
app.include_router(materias.router)
app.include_router(observaciones.router)
app.include_router(plan_de_clases.router)
app.include_router(dashboard.router)
app.include_router(planeador_anual.router)
app.include_router(usuario.router)
app.include_router(reportes.router)
app.include_router(super_admin.router)
app.include_router(tenant.router)
app.include_router(tipos_pagos.router)
app.include_router(inventario.router)
app.include_router(egresos.router)
app.include_router(prestamos.router)
app.include_router(ventas.router)
app.include_router(nomina.router, prefix="/api/nomina")
app.include_router(boletines.router)
app.include_router(branding.router)
app.include_router(plantillas.router)
app.include_router(cartera.router)


