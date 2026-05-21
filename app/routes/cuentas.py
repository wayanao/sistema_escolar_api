from fastapi import APIRouter, Depends
from app.dependencies import get_current_active_admin

# 👇 importamos controllers
from app.controllers.estado_cuenta_controller import (
    estado_cuenta_curso_controller,
    estado_cuenta_estudiante_controller
)

router = APIRouter(tags=["Cuentas"], dependencies=[Depends(get_current_active_admin)])


# 📊 Estado por curso
@router.get("/estado-cuenta/curso/{curso_id}")
def estado_cuenta_curso(curso_id: int):

    return estado_cuenta_curso_controller(curso_id)


# 👤 Estado por estudiante
@router.get("/estado-cuenta/estudiante/{estudiante_id}")
def estado_cuenta_estudiante(estudiante_id: int):

    return estado_cuenta_estudiante_controller(estudiante_id)

