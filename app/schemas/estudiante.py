from pydantic import BaseModel
from datetime import date
from typing import Optional

class EstudianteCreate(BaseModel):
    nombre: str
    apellido: str
    documento_identidad: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    curso_id: int

    # opcionales
    descuento_matricula: float = 0
    descuento_mensualidad: float = 0
    datos_medicos: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    nombre_padre: Optional[str] = None
    telefono_padre: Optional[str] = None
    nombre_madre: Optional[str] = None
    telefono_madre: Optional[str] = None
    contacto_emergencia: Optional[str] = None

    tipo_documento: Optional[str] = None
    lugar_expedicion: Optional[str] = None
    eps: Optional[str] = None
    estrato: Optional[str] = None
    jornada: Optional[str] = None
    
    colegio_anterior: Optional[str] = None
    anio_cursado_anterior: Optional[str] = None
    pre_escolar_anterior: Optional[str] = None
    ebp_anterior: Optional[str] = None
    motivo_retiro_anterior: Optional[str] = None
    paz_salvo_anterior: Optional[str] = None
    
    ocupacion_padre: Optional[str] = None
    tipo_documento_padre: Optional[str] = None
    documento_padre: Optional[str] = None
    
    ocupacion_madre: Optional[str] = None
    tipo_documento_madre: Optional[str] = None
    documento_madre: Optional[str] = None

    condicion_diagnostico: Optional[str] = None

