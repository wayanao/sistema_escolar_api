import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import jwt, JWTError

from app.config import settings
from app.core.logging import configure_logging
from app.database import close_pool
from app.db.tenant import TENANT_SCHEMA_PATTERN
from app.globals import tenant_schema_var

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
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Inicializar limiter en la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 🔥 CORS (SOLO UNA VEZ)
origins = [
    settings.FRONTEND_URL,
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

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
