"""Endpoints de salud: `/ping` para el monitor externo y `/health` a mano.

Son publicos a proposito: un monitor no puede iniciar sesion. Por eso la
respuesta se limita a un estado y no expone version, host ni detalle de error.

`GET /ping` responde `200` si la API atiende, sin tocar la base. Es la que
llama el monitor: Neon cobra mientras la base esta despierta, y un chequeo que
la consultara cada 5 minutos no la dejaria dormir nunca.

`GET /health` responde `200` cuando la API vive y la base contesta, y `503`
cuando la base falla. Queda para comprobar a mano, por ejemplo tras publicar.

Aviso operativo: **no** usar `/health` como `Health Check Path` de Render.
Render reinicia el servicio cuando ese chequeo falla, de modo que un bache de
la base provocaria reinicios en cadena y agravaria la caida. El chequeo de la
plataforma debe quedar vacio.
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
    para cualquier monitor o revision a mano y evita que un tercero ocupe con
    esta ruta los trabajadores del threadpool.
    """
    if not check_database():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "error"},
        )

    return {"status": "ok", "database": "ok"}


@router.get("/ping")
@limiter.limit("60/minute")
def ping(request: Request):
    """La API atiende. No toca la base, a proposito.

    Neon duerme la base tras 5 minutos sin consultas y cobra mientras esta
    despierta. UptimeRobot llamaba a `/health` cada 5 minutos y la base no se
    durmio nunca: en Monitoring de Neon, tres dias seguidos sin un solo tramo
    inactivo (visto el 2026-11-03).

    Es sincrona para pasar por los mismos hilos que el resto de la API: si
    estan todos ocupados, `/ping` tambien espera y el monitor lo nota. El
    limite es el mismo de `/health`, por la misma razon.

    No detecta que la base falle ni que el pool se agote: eso solo lo ve
    `/health`.
    """
    return {"status": "ok"}
