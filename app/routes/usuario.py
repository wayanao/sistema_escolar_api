from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, HTTPException
from app.controllers.usuario_controller import (
    crear_usuario_controller,
    obtener_usuarios_controller,
    actualizar_usuario_controller,
    eliminar_usuario_controller
)
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate

router = APIRouter(tags=["Usuario"], dependencies=[Depends(get_current_user)])

@router.post("/usuarios")
def crear_usuario(usuario: UsuarioCreate):
    try:
        return crear_usuario_controller(usuario)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/usuarios")
def obtener_usuarios():
    try:
        return obtener_usuarios_controller()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/usuarios/{user_id}")
def actualizar_usuario(user_id: int, usuario: UsuarioUpdate):
    try:
        return actualizar_usuario_controller(user_id, usuario)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/usuarios/{user_id}")
def eliminar_usuario(user_id: int):
    try:
        return eliminar_usuario_controller(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))