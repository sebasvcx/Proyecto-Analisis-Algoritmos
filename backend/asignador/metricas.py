"""Puntajes para comparar resultados (Sección 5.4) y medidas del resultado (5.5).

Se calculan sobre la salida serializada, igual que el verificador: solo usan los
identificadores de sección de la salida, no el estado interno del algoritmo.
"""

from __future__ import annotations

from . import satisfaccion
from .dominio import Instancia

PRIORIDADES = (5, 4, 3, 2, 1)


def agregar_satisfaccion(instancia: Instancia, estudiantes_salida: list[dict]) -> None:
    """Agrega a cada estudiante de la salida su campo `satisfaccion` (Sección 5.5)."""
    secciones_de = {
        res["id"]: [r["seccion"] for r in res["solicitudes"] if r.get("seccion") in instancia.secciones]
        for res in estudiantes_salida
    }
    for res in estudiantes_salida:
        estudiante = instancia.estudiantes.get(res["id"])
        if estudiante is None:
            continue
        secciones = [instancia.secciones[sid] for sid in secciones_de[res["id"]]]
        res["satisfaccion"] = satisfaccion.calcular(instancia, estudiante, secciones, secciones_de).como_dict()


def resumir_satisfaccion(estudiantes_salida: list[dict]) -> dict:
    """Promedio y mínimo entre estudiantes con algún criterio evaluable de peso positivo."""
    evaluables = [res["satisfaccion"] for res in estudiantes_salida if res.get("satisfaccion", {}).get("evaluable")]
    totales = [s["total"] for s in evaluables]
    por_criterio = {}
    for c in satisfaccion.CRITERIOS:
        valores = [s["criterios"][c]["valor"] for s in evaluables if s["criterios"][c]["evaluable"]]
        por_criterio[c] = round(sum(valores) / len(valores), 4) if valores else None
    return {
        "estudiantes_evaluables": len(evaluables),
        "promedio": round(sum(totales) / len(totales), 4) if totales else None,
        "minimo": round(min(totales), 4) if totales else None,
        "por_criterio": por_criterio,
    }


def _aporte(estado: str, valor_sustituta: float) -> float:
    return {"principal": 1.0, "sustituida": valor_sustituta}.get(estado, 0.0)


def calcular_metricas(instancia: Instancia, estudiantes_salida: list[dict]) -> dict:
    cfg = instancia.configuracion
    c = {k: 0.0 for k in PRIORIDADES}
    pedidas_por_prioridad = {k: 0 for k in PRIORIDADES}
    principales = sustituidas = pendientes = 0
    suma_ponderada = suma_prioridades = 0.0

    for res in estudiantes_salida:
        for r in res["solicitudes"]:
            k = r["prioridad"]
            aporte = _aporte(r["estado"], cfg.valor_sustituta)
            c[k] += aporte
            pedidas_por_prioridad[k] += 1
            suma_ponderada += aporte * k
            suma_prioridades += k
            if r["estado"] == "principal":
                principales += 1
            elif r["estado"] == "sustituida":
                sustituidas += 1
            else:
                pendientes += 1

    total = principales + sustituidas + pendientes
    return {
        # Q (primer componente): vector lexicográfico (C5, C4, C3, C2, C1)
        "puntaje_lexicografico": [round(c[k], 4) for k in PRIORIDADES],
        "por_prioridad": [
            {"prioridad": k, "pedidas": pedidas_por_prioridad[k], "puntaje": round(c[k], 4)} for k in PRIORIDADES
        ],
        "solicitudes": {"total": total, "principales": principales, "sustituidas": sustituidas, "pendientes": pendientes},
        "cobertura": round((principales + sustituidas) / total, 4) if total else None,
        "indicador_academico": round(suma_ponderada / suma_prioridades, 4) if suma_prioridades else None,
        "satisfaccion": resumir_satisfaccion(estudiantes_salida),
    }


def comparar(q_a: list[float], q_b: list[float]) -> int:
    """Orden lexicográfico: 1 si A es mejor, -1 si B es mejor, 0 si empatan."""
    for a, b in zip(q_a, q_b):
        if abs(a - b) > 1e-9:
            return 1 if a > b else -1
    return 0
