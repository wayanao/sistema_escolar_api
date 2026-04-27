from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.controllers.auth_controller import login_controller
from app.security import create_access_token

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class Login(BaseModel):
    email: str
    password: str
    codigo_colegio: str

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: Login):
    # Pasamos el código de colegio al controlador de login
    user = login_controller(data.email, data.password, data.codigo_colegio)

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

    return {
        "id": user["id"],
        "nombre": user["nombre"],
        "rol": user["rol"],
        "tenant": user["tenant"],
        "access_token": access_token,
        "token_type": "bearer"
    }