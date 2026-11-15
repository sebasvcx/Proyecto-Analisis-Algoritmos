"""Puntajes para comparar resultados (Sección 5.4) y medidas del resultado (5.5).

Se calculan sobre la salida serializada, igual que el verificador.
La satisfacción de preferencias se agregará con los niveles 5 a 9.
"""

from __future__ import annotations

from .dominio import Instancia

PRIORIDADES = (5, 4, 3, 2, 1)


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
    }


def comparar(q_a: list[float], q_b: list[float]) -> int:
    """Orden lexicográfico: 1 si A es mejor, -1 si B es mejor, 0 si empatan."""
    for a, b in zip(q_a, q_b):
        if abs(a - b) > 1e-9:
            return 1 if a > b else -1
    return 0
