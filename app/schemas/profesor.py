from typing import Literal, Optional

from pydantic import BaseModel, EmailStr

EstadoProfesor = Literal["activo", "inactivo"]

# 🎯 Schema para crear profesor
class ProfesorCreate(BaseModel):
    nombre: str
    apellido: str
    documento_identidad: str
    email: EmailStr  # 📧 validación automática de email
    telefono: str
    password: str  # 🔒 en un caso real, esto debería ser un hash
    sueldo: float = 0.0  # 💵 Sueldo del profesor
    estado: Optional[EstadoProfesor] = None


class ProfesorEstadoUpdate(BaseModel):
    estado: EstadoProfesor
