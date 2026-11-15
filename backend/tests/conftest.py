from __future__ import annotations

import pytest

from asignador.corrida import ejecutar_corrida
from asignador.datos import cargar_instancia


@pytest.fixture
def correr():
    """Carga los datos crudos y ejecuta el nivel pedido. Devuelve la salida serializada."""

    def _correr(crudos: dict, nivel: int) -> dict:
        return ejecutar_corrida(cargar_instancia(crudos), nivel)

    return _correr


def solicitud(salida: dict, eid: str, materia: str) -> dict:
    est = next(e for e in salida["estudiantes"] if e["id"] == eid)
    return next(s for s in est["solicitudes"] if s["materia"] == materia)


def aviso(salida: dict, eid: str, materia: str) -> dict | None:
    est = next(e for e in salida["estudiantes"] if e["id"] == eid)
    return next((a for a in est["avisos"] if a["materia"] == materia), None)
