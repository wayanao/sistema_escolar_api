from pydantic import BaseModel


class CopiarConfiguracionAnio(BaseModel):
    """Opciones adicionales; cursos y conceptos se copian siempre."""

    copiar_precios: bool = False
    copiar_carga_academica: bool = False
    copiar_directores: bool = False
