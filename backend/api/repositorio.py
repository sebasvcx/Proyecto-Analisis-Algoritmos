"""Acceso a la carpeta `data/`: única fuente de verdad de la aplicación."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from asignador.datos import ARCHIVOS, construir_instancia, escribir_carpeta, leer_carpeta, respaldar_carpeta
from asignador.datos.archivos import OPCIONALES
from asignador.dominio import Instancia


class RepositorioDatos:
    def __init__(self, carpeta: Path, respaldos: Path):
        self.carpeta = carpeta
        self.respaldos = respaldos

    def leer(self) -> tuple[dict[str, Any], dict[str, str]]:
        return leer_carpeta(self.carpeta)

    def leer_entidad(self, entidad: str) -> Any:
        crudos, _ = self.leer()
        return crudos.get(entidad)

    def cargar(self) -> tuple[Instancia | None, Any, dict[str, Any]]:
        crudos, fallos = self.leer()
        instancia, reporte = construir_instancia(crudos, fallos)
        return instancia, reporte, crudos

    def reemplazar(self, cambios: dict[str, Any]) -> Path | None:
        """Respalda los archivos actuales y escribe los nuevos."""
        respaldo = respaldar_carpeta(self.carpeta, self.respaldos)
        escribir_carpeta(self.carpeta, cambios)
        return respaldo

    def resumen(self) -> dict:
        _, reporte, crudos = self.cargar()
        archivos = []
        for entidad, nombre in ARCHIVOS.items():
            contenido = crudos.get(entidad)
            archivos.append(
                {
                    "entidad": entidad,
                    "archivo": nombre,
                    "opcional": entidad in OPCIONALES,
                    "presente": contenido is not None,
                    "registros": len(contenido) if isinstance(contenido, list) else None,
                }
            )
        return {
            "archivos": archivos,
            "validacion": {
                "errores": len(reporte.errores),
                "advertencias": len(reporte.advertencias),
                "problemas": [p.como_dict() for p in reporte.problemas],
            },
            "configuracion": crudos.get("config") or {},
        }
