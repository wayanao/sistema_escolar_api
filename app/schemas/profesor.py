from pydantic import BaseModel, EmailStr

# 🎯 Schema para crear profesor
class ProfesorCreate(BaseModel):
    nombre: str
    apellido: str
    documento_identidad: str
    email: EmailStr  # 📧 validación automática de email
    telefono: str
    password: str  # 🔒 en un caso real, esto debería ser un hash
    sueldo: float = 0.0  # 💵 Sueldo del profesor