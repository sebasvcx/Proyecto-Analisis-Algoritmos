"""Rutas de almacenamiento. Se pueden cambiar con variables de entorno (útil en Docker)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Ajustes:
    carpeta_datos: Path
    carpeta_resultados: Path
    carpeta_respaldos: Path
    origenes_cors: tuple[str, ...]


@lru_cache
def obtener_ajustes() -> Ajustes:
    datos = Path(os.getenv("ASIGNADOR_DATOS", RAIZ_PROYECTO / "data"))
    return Ajustes(
        carpeta_datos=datos,
        carpeta_resultados=Path(os.getenv("ASIGNADOR_RESULTADOS", RAIZ_PROYECTO / "resultados")),
        carpeta_respaldos=Path(os.getenv("ASIGNADOR_RESPALDOS", datos / ".respaldos")),
        origenes_cors=tuple(os.getenv("ASIGNADOR_CORS", "http://localhost:5173").split(",")),
    )
