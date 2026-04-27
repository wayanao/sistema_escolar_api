from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import jwt, JWTError

from app.config import settings
from app.globals import tenant_schema_var

from app.routes import inventario, estudiantes
from app.routes import inventario, cuentas
from app.routes import inventario, pagos
from app.routes import inventario, cursos
from app.routes import inventario, profesores
from app.routes import inventario, asignaciones
from app.routes import inventario, notas
from app.routes import inventario, planilla
from app.routes import inventario, asistencia
from app.routes import inventario, auth
from app.routes import inventario, materias
from app.routes import inventario, observaciones
from app.routes import inventario, plan_de_clases
from app.routes import inventario, dashboard
from app.routes import inventario, planeador_anual
from app.routes import inventario, usuario
from app.routes import inventario, reportes
from app.routes import inventario, tipos_pagos
from app.routes import egresos, prestamos, ventas, nomina

# Configuración de Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI()

print("FRONTEND_URL:", settings.FRONTEND_URL)  # 👈 AQUÍ

# Inicializar limiter en la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 🔥 CORS (SOLO UNA VEZ)
origins = [
    settings.FRONTEND_URL
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
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            tenant = payload.get("tenant")
            if tenant:
                # Fijamos el contexto a nivel raíz de HTTP
                tenant_schema_var.set(tenant)
        except JWTError:
            pass  # Si el token es inválido, lo ignoramos (fastapi/Depends validará y lanzará 401 después)
    
    # Procesar la petición
    response = await call_next(request)
    return response

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


from app.routes import boletines
app.include_router(boletines.router)
