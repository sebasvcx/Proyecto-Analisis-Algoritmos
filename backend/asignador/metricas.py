"""Puntajes para comparar resultados (Sección 5.4) y medidas del resultado (5.5).

Se calculan sobre la salida serializada, igual que el verificador: solo usan los
identificadores de sección de la salida, no el estado interno del algoritmo.
"""

from __future__ import annotations

from . import objetivo, satisfaccion
from .dominio import Instancia

PRIORIDADES = (5, 4, 3, 2, 1)


def registros_de_salida(instancia: Instancia, estudiantes_salida: list[dict]) -> list[objetivo.Registro]:
    """Convierte la salida serializada en registros para calcular Q (Sección 5.4)."""
    registros = []
    for res in estudiantes_salida:
        estudiante = instancia.estudiantes.get(res["id"])
        if estudiante is None:
            continue
        sustitutas = {s.materia: s.sustitutas for s in estudiante.solicitudes}
        for r in res["solicitudes"]:
            if r["materia"] not in sustitutas:
                continue
            posicion = None
            if r["estado"] == "sustituida":
                inscrita = r.get("materia_inscrita") or instancia.secciones[r["seccion"]].materia
                posicion = sustitutas[r["materia"]].index(inscrita) if inscrita in sustitutas[r["materia"]] else None
            seccion = r["seccion"] if r["estado"] != "no_inscrita" else None
            registros.append(objetivo.Registro(res["id"], r["materia"], seccion, posicion))
    return registros


def puntaje(instancia: Instancia, estudiantes_salida: list[dict]) -> objetivo.Puntaje:
    """Q completo de una salida que ya tiene el campo `satisfaccion` de cada estudiante."""
    total = sum(res.get("satisfaccion", {}).get("total", satisfaccion.NEUTRO) for res in estudiantes_salida)
    return objetivo.puntuar(instancia, registros_de_salida(instancia, estudiantes_salida), total)


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
        # Q completo en el orden de la Sección 5.4 (para comparar corridas entre sí)
        "objetivo": puntaje(instancia, estudiantes_salida).como_dict(),
    }
