"""Representación del tiempo semanal.

Las horas se manejan internamente como minutos desde la medianoche para que
las comparaciones de cruces y traslados sean aritmética entera simple.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DIAS: tuple[str, ...] = ("L", "M", "X", "J", "V", "S")
NOMBRES_DIA = {"L": "Lunes", "M": "Martes", "X": "Miércoles", "J": "Jueves", "V": "Viernes", "S": "Sábado"}
TODOS_LOS_DIAS = "*"

HORA_APERTURA = 7 * 60  # 07:00
HORA_CIERRE = 20 * 60  # 20:00
DURACION_SESION = 2 * 60  # cada sesión dura dos horas
SALIDA_ANTICIPADA = 10  # minutos que una clase termina antes de su hora oficial

_PATRON_HORA = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def a_minutos(hora: str) -> int:
    """Convierte 'HH:MM' en minutos desde la medianoche."""
    coincidencia = _PATRON_HORA.match(hora)
    if not coincidencia:
        raise ValueError(f"hora inválida '{hora}', se espera HH:MM")
    return int(coincidencia.group(1)) * 60 + int(coincidencia.group(2))


def a_hora(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


@dataclass(frozen=True, order=True)
class Franja:
    """Un intervalo [inicio, fin) dentro de un día de la semana."""

    dia: str
    inicio: int
    fin: int

    def duracion(self) -> int:
        return self.fin - self.inicio

    def se_cruza_con(self, otra: Franja) -> bool:
        # Mismo día y cada una empieza antes de que termine la otra:
        # 07:00-09:00 y 09:00-11:00 NO se cruzan.
        return self.dia == otra.dia and self.inicio < otra.fin and otra.inicio < self.fin

    def contiene(self, otra: Franja) -> bool:
        return self.dia == otra.dia and self.inicio <= otra.inicio and otra.fin <= self.fin

    def __str__(self) -> str:
        return f"{self.dia} {a_hora(self.inicio)}-{a_hora(self.fin)}"


def expandir_dias(dia: str) -> tuple[str, ...]:
    """El día '*' equivale a lunes a sábado."""
    return DIAS if dia == TODOS_LOS_DIAS else (dia,)
