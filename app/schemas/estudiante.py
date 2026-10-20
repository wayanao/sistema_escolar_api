from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import Literal, Optional

EstadoEstudiante = Literal["activo", "retirado", "egresado", "inactivo"]

# SISBÉN y lugar de residencia (docs/funcionalidades/SISBEN_RESIDENCIA.md).
GrupoSisben = Literal["A", "B", "C", "D"]
ZonaResidencia = Literal["urbana", "rural"]
# Subgrupos del SISBÉN IV: A1 a A5, B1 a B7, C1 a C18 y D1 a D21.
ULTIMO_SUBGRUPO_SISBEN = {"A": 5, "B": 7, "C": 18, "D": 21}


def _subgrupo_valido(grupo, subgrupo):
    numero = subgrupo[1:]
    return (
        subgrupo[:1] == grupo
        and numero.isdigit()
        and not numero.startswith("0")
        and int(numero) <= ULTIMO_SUBGRUPO_SISBEN[grupo]
    )


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
    estado: Optional[EstadoEstudiante] = None

    # SISBÉN y lugar de residencia. Se guardan aparte de los 34 datos de
    # arriba y solo si llegó alguno (ver
    # `estudiante_controller.guardar_sisben_y_residencia_si_llegaron`).
    sisben: Optional[bool] = None
    sisben_grupo: Optional[GrupoSisben] = None
    sisben_subgrupo: Optional[str] = Field(default=None, max_length=3)
    sisben_nivel: Optional[int] = Field(default=None, ge=1, le=3)
    barrio: Optional[str] = Field(default=None, max_length=150)
    municipio: Optional[str] = Field(default=None, max_length=100)
    zona_residencia: Optional[ZonaResidencia] = None
    punto_referencia: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def revisar_sisben(self):
        clasificacion = (self.sisben_grupo, self.sisben_subgrupo, self.sisben_nivel)
        if self.sisben is not True and any(dato is not None for dato in clasificacion):
            raise ValueError(
                "Sin SISBÉN no se guarda grupo, subgrupo ni nivel. "
                "Marca que sí tiene SISBÉN o quítalos."
            )
        if self.sisben_subgrupo is None:
            return self
        grupo = self.sisben_grupo
        if grupo is None:
            raise ValueError("Para el subgrupo del SISBÉN hace falta el grupo.")
        if not _subgrupo_valido(grupo, self.sisben_subgrupo):
            raise ValueError(
                f"El subgrupo {self.sisben_subgrupo} no existe: el grupo {grupo} "
                f"va de {grupo}1 a {grupo}{ULTIMO_SUBGRUPO_SISBEN[grupo]}."
            )
        return self


class EstudianteEstadoUpdate(BaseModel):
    estado: EstadoEstudiante

