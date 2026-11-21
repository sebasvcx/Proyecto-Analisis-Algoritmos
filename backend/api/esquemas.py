"""Cuerpos de las peticiones (validados por Pydantic)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from asignador.generador import Escasez
from asignador.referencias import Referencia


class PeticionGenerar(BaseModel):
    estudiantes: int = Field(250, ge=0, le=5000)
    secciones: int = Field(96, ge=42, le=1000)
    porcentaje_trabaja: float = Field(0.2, ge=0, le=1)
    escasez: Escasez = Escasez.AJUSTADA
    semilla: int = Field(42, ge=0)


class PeticionCorrida(BaseModel):
    nivel: int = Field(2, ge=1, le=10)
    # Si se indica, reemplaza el valor de config.json solo para esta corrida (casilla de N10)
    desempate_semestre: bool | None = None
    # Si se indica, en lugar de un nivel se ejecuta una asignación de referencia (Sección 7.3)
    referencia: Referencia | None = None
    semilla_referencia: int = Field(0, ge=0)
