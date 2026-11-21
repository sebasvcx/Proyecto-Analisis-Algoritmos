"""Orquesta una corrida completa: asignar → serializar → verificar → medir.

Es lo que llaman tanto la API como la línea de comandos.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from . import __version__
from .algoritmo import Asignacion, Horario, asignar
from .datos.archivos import ARCHIVOS, escribir_json
from .dominio import Instancia
from .metricas import agregar_satisfaccion, calcular_metricas
from .verificador import verificar


def _estado(horario: Horario, solicitud) -> tuple[str, str | None, str | None]:
    inscripcion = horario.inscripcion_de(solicitud)
    if inscripcion is None:
        return "no_inscrita", None, None
    estado = "sustituida" if inscripcion.es_sustituta else "principal"
    return estado, inscripcion.seccion.id, inscripcion.materia


def serializar_horario(horario: Horario) -> dict:
    est = horario.estudiante
    solicitudes = []
    for sol in sorted(est.solicitudes, key=lambda s: (-s.prioridad, s.materia)):
        estado, seccion, materia_inscrita = _estado(horario, sol)
        solicitudes.append(
            {"materia": sol.materia, "prioridad": sol.prioridad, "estado": estado, "seccion": seccion, "materia_inscrita": materia_inscrita}
        )
    avisos = [
        {
            "materia": a.solicitud.materia,
            "causa": a.causa.texto,
            "sugerencia": a.causa.sugerencia,
            "causas": [c.texto for c in a.todas],
            "sustituta": a.sustituta,
        }
        for a in horario.avisos
    ]
    return {"id": est.id, "creditos": horario.creditos(), "solicitudes": solicitudes, "avisos": avisos}


def serializar(asignacion: Asignacion) -> tuple[list[dict], list[dict]]:
    estudiantes = [serializar_horario(h) for h in asignacion.horarios.values()]
    inst = asignacion.contexto.instancia
    secciones = [
        {"id": s.id, "materia": s.materia, "cupo": s.cupo, "inscritos": asignacion.contexto.inscritos[s.id]}
        for s in sorted(inst.secciones.values(), key=lambda s: s.id)
    ]
    return estudiantes, secciones


def ejecutar_corrida(instancia: Instancia, numero_nivel: int, identificador: str | None = None) -> dict[str, Any]:
    inicio = time.perf_counter()
    asignacion = asignar(instancia, numero_nivel)
    tiempo_algoritmo = time.perf_counter() - inicio
    return armar_salida(instancia, asignacion, tiempo_algoritmo, identificador)


def armar_salida(
    instancia: Instancia, asignacion: Asignacion, tiempo_algoritmo: float, identificador: str | None = None, sufijo: str | None = None
) -> dict[str, Any]:
    """Serializa, verifica y mide una asignación (del algoritmo o de una referencia)."""
    estudiantes, secciones = serializar(asignacion)
    agregar_satisfaccion(instancia, estudiantes)

    inicio = time.perf_counter()
    verificacion = verificar(instancia, estudiantes)
    tiempo_verificacion = time.perf_counter() - inicio

    nivel = asignacion.nivel
    ahora = datetime.now()
    return {
        "corrida": {
            "id": identificador or ahora.strftime("%Y%m%d-%H%M%S") + f"-{sufijo or f'n{nivel.numero}'}",
            "fecha": ahora.isoformat(timespec="seconds"),
            "nivel": nivel.numero,
            "nombre_nivel": nivel.nombre,
            "reglas_del_nivel": list(nivel.reglas_cubiertas),
            "version": __version__,
            "configuracion": asdict(instancia.configuracion),
            "tiempo_algoritmo_s": round(tiempo_algoritmo, 4),
            "tiempo_verificacion_s": round(tiempo_verificacion, 4),
            "estudiantes": len(instancia.estudiantes),
            "secciones": len(instancia.secciones),
            "mejora": asignacion.mejora,  # solo N10: cambios examinados y aceptados
        },
        "resumen": calcular_metricas(instancia, estudiantes),
        "verificacion": verificacion.como_dict(),
        "estudiantes": estudiantes,
        "secciones": secciones,
    }


def guardar_corrida(carpeta_resultados: Path, salida: dict, entradas: dict[str, Any]) -> Path:
    """Guarda `resultados/<id>/salida.json` y una copia de las entradas usadas."""
    destino = carpeta_resultados / salida["corrida"]["id"]
    escribir_json(destino / "salida.json", salida)
    for entidad, contenido in entradas.items():
        escribir_json(destino / "entrada" / ARCHIVOS[entidad], contenido)
    return destino


def leer_corrida(carpeta_resultados: Path, identificador: str) -> dict | None:
    ruta = carpeta_resultados / identificador / "salida.json"
    if not ruta.is_file() or ruta.parent.parent.resolve() != carpeta_resultados.resolve():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def leer_entrada_corrida(carpeta_resultados: Path, identificador: str, entidad: str) -> Any | None:
    """Entradas con las que se ejecutó la corrida (pueden diferir de las actuales en data/)."""
    if entidad not in ARCHIVOS:
        return None
    ruta = carpeta_resultados / identificador / "entrada" / ARCHIVOS[entidad]
    if not ruta.is_file() or ruta.parents[2].resolve() != carpeta_resultados.resolve():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def listar_corridas(carpeta_resultados: Path) -> list[dict]:
    if not carpeta_resultados.exists():
        return []
    corridas = []
    for ruta in sorted(carpeta_resultados.glob("*/salida.json"), reverse=True):
        salida = json.loads(ruta.read_text(encoding="utf-8"))
        corridas.append(
            {
                **{k: salida["corrida"][k] for k in ("id", "fecha", "nivel", "nombre_nivel", "estudiantes")},
                "referencia": salida["corrida"].get("referencia"),
                "desempate_semestre": salida["corrida"]["configuracion"].get("desempate_semestre", False),
                "cobertura": salida["resumen"]["cobertura"],
                "violaciones": salida["verificacion"]["total"],
            }
        )
    return corridas

