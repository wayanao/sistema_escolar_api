"""Endpoint de salud para monitoreo externo.

Es publico a proposito: un monitor no puede iniciar sesion. Por eso la
respuesta se limita a un estado y no expone version, host ni detalle de error.

`GET /health` responde `200` cuando la API vive y la base contesta, y `503`
cuando la base falla. Un monitor externo alerta con cualquier codigo distinto
de `200`, asi que el aviso llega sin configurar nada mas.

Aviso operativo: **no** usar esta ruta como `Health Check Path` de Render.
Render reinicia el servicio cuando ese chequeo falla, de modo que un bache de
la base provocaria reinicios en cadena y agravaria la caida. Esta ruta es para
el monitor externo; el chequeo de la plataforma debe quedar vacio.
"""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.health import check_database

router = APIRouter(tags=["Health"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/health")
@limiter.limit("60/minute")
def health(request: Request):
    """Estado de la API y de su base de datos.

    El limite es explicito porque el `default_limits` del limitador de
    `main.py` no se aplica: requiere `SlowAPIMiddleware`, que la app no monta,
    asi que hoy solo los endpoints decorados quedan limitados. 60/minuto sobra
    para cualquier monitor —UptimeRobot consulta cada 5 minutos— y evita que un
    tercero ocupe con esta ruta los trabajadores del threadpool.
    """
    if not check_database():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "error"},
        )

    return {"status": "ok", "database": "ok"}
