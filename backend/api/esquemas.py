"""Cuerpos de las peticiones (validados por Pydantic)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from asignador.generador import Escasez


class PeticionGenerar(BaseModel):
    estudiantes: int = Field(250, ge=0, le=5000)
    secciones: int = Field(96, ge=42, le=1000)
    porcentaje_trabaja: float = Field(0.2, ge=0, le=1)
    escasez: Escasez = Escasez.AJUSTADA
    semilla: int = Field(42, ge=0)


class PeticionCorrida(BaseModel):
    nivel: int = Field(2, ge=1, le=10)
