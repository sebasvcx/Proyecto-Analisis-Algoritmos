"""Lectura y escritura de la carpeta `data/` (almacenamiento local en JSON)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

# entidad -> nombre de archivo
ARCHIVOS: dict[str, str] = {
    "materias": "materias.json",
    "profesores": "profesores.json",
    "edificios": "edificios.json",
    "traslados": "traslados.json",
    "secciones": "secciones.json",
    "estudiantes": "estudiantes.json",
    "config": "config.json",
}
OPCIONALES = frozenset({"config"})


def leer_carpeta(carpeta: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Lee todos los JSON conocidos.

    Devuelve (contenido por entidad, errores de lectura por entidad). Un archivo
    ausente u ilegible no detiene la lectura de los demás.
    """
    crudos: dict[str, Any] = {}
    fallos: dict[str, str] = {}
    for entidad, nombre in ARCHIVOS.items():
        ruta = carpeta / nombre
        if not ruta.exists():
            if entidad not in OPCIONALES:
                fallos[entidad] = "el archivo no existe"
            continue
        try:
            crudos[entidad] = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fallos[entidad] = f"JSON mal formado (línea {exc.lineno}, columna {exc.colno})"
    return crudos, fallos


def escribir_json(ruta: Path, contenido: Any) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(json.dumps(contenido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporal.replace(ruta)  # reemplazo atómico: nunca queda un archivo a medias


def escribir_carpeta(carpeta: Path, crudos: dict[str, Any]) -> None:
    for entidad, contenido in crudos.items():
        escribir_json(carpeta / ARCHIVOS[entidad], contenido)


def respaldar_carpeta(carpeta: Path, destino_raiz: Path) -> Path | None:
    """Copia los JSON actuales a `destino_raiz/<fecha>/` antes de reemplazarlos."""
    existentes = [carpeta / n for n in ARCHIVOS.values() if (carpeta / n).exists()]
    if not existentes:
        return None
    destino = destino_raiz / datetime.now().strftime("%Y%m%d-%H%M%S")
    destino.mkdir(parents=True, exist_ok=True)
    for ruta in existentes:
        shutil.copy2(ruta, destino / ruta.name)
    return destino
