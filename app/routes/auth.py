from fastapi import APIRouter, HTTPException, status, Request, Response
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings
from app.controllers.auth_controller import login_controller
from app.core.tenant_status import TenantLoginBlocked
from app.security import create_access_token

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class Login(BaseModel):
    email: str
    password: str
    codigo_colegio: str

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, response: Response, data: Login):
    # Pasamos el código de colegio al controlador de login
    try:
        user = login_controller(data.email, data.password, data.codigo_colegio)
    except TenantLoginBlocked as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "tenant_blocked",
                "estado": exc.estado,
                "message": exc.message,
            },
        ) from exc

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o código de colegio inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crear token de acceso incluyendo el esquema de BD 
    access_token = create_access_token(
        data={
            "sub": str(user["id"]), 
            "rol": user["rol"],
            "tenant": user["tenant"]   # <--- Nueva variable guardada en el token
        }
    )

    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {
        "id": user["id"],
        "nombre": user["nombre"],
        "rol": user["rol"],
        "tenant": user["tenant"],
        "tenant_estado": user.get("tenant_estado"),
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        "token",
        path="/",
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    return {"mensaje": "Sesion cerrada"}
