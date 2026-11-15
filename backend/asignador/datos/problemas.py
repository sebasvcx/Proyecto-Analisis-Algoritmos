"""Errores y advertencias encontrados al cargar una instancia."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class Gravedad(str, Enum):
    ERROR = "error"  # impide ejecutar
    ADVERTENCIA = "advertencia"  # se informa, pero se puede ejecutar


@dataclass(frozen=True)
class Problema:
    archivo: str
    registro: str
    campo: str
    mensaje: str
    gravedad: Gravedad = Gravedad.ERROR

    def como_dict(self) -> dict:
        datos = asdict(self)
        datos["gravedad"] = self.gravedad.value
        return datos

    def __str__(self) -> str:
        donde = " › ".join(p for p in (self.archivo, self.registro, self.campo) if p)
        return f"{donde}: {self.mensaje}"


@dataclass
class Reporte:
    problemas: list[Problema] = field(default_factory=list)

    def error(self, archivo: str, registro: str, campo: str, mensaje: str) -> None:
        self.problemas.append(Problema(archivo, registro, campo, mensaje))

    def advertencia(self, archivo: str, registro: str, campo: str, mensaje: str) -> None:
        self.problemas.append(Problema(archivo, registro, campo, mensaje, Gravedad.ADVERTENCIA))

    @property
    def errores(self) -> list[Problema]:
        return [p for p in self.problemas if p.gravedad is Gravedad.ERROR]

    @property
    def advertencias(self) -> list[Problema]:
        return [p for p in self.problemas if p.gravedad is Gravedad.ADVERTENCIA]

    @property
    def es_valido(self) -> bool:
        return not self.errores


class DatosInvalidos(Exception):
    """Se lanza cuando la instancia tiene errores que impiden ejecutar."""

    def __init__(self, reporte: Reporte):
        self.reporte = reporte
        resumen = "; ".join(str(p) for p in reporte.errores[:5])
        super().__init__(f"{len(reporte.errores)} error(es) en los datos: {resumen}")
