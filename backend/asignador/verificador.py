"""Verificador independiente de reglas (Sección 5.6).

Recibe la SALIDA serializada (la misma que se guarda en `resultados/`) y la
instancia, y recalcula las reglas sin reutilizar el código del algoritmo.
Así un error en `algoritmo/reglas.py` no se oculta a sí mismo.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from itertools import combinations

from .dominio import Instancia

REGLAS_VERIFICADAS = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9")
MINUTOS_SALIDA_ANTICIPADA = 10  # Sección 5.3, condición 4 (se repite a propósito: no se importa del algoritmo)
ESTADOS = ("principal", "sustituida", "no_inscrita")


@dataclass(frozen=True)
class Violacion:
    regla: str  # R1..R9, o "E" para errores de estructura de la salida
    estudiante: str
    detalle: str
    seccion: str | None = None


@dataclass
class Verificacion:
    reglas: tuple[str, ...] = REGLAS_VERIFICADAS
    violaciones: list[Violacion] = field(default_factory=list)

    def por_regla(self) -> dict[str, int]:
        conteo = Counter(v.regla for v in self.violaciones)
        resumen = {r: conteo.get(r, 0) for r in self.reglas}
        if conteo.get("E"):
            resumen["E"] = conteo["E"]
        return resumen

    def como_dict(self, limite: int = 200) -> dict:
        return {
            "reglas_verificadas": list(self.reglas),
            "total": len(self.violaciones),
            "por_regla": self.por_regla(),
            "violaciones": [asdict(v) for v in self.violaciones[:limite]],
        }


def _cruzan(a: dict, b: dict) -> bool:
    return a["dia"] == b["dia"] and a["inicio"] < b["fin"] and b["inicio"] < a["fin"]


def _consecutivas(planas: list[tuple[str, dict]]) -> list[tuple[tuple[str, dict], tuple[str, dict]]]:
    """Pares de sesiones que quedan una detrás de otra en el mismo día."""
    por_dia: dict[str, list[tuple[str, dict]]] = {}
    for item in planas:
        por_dia.setdefault(item[1]["dia"], []).append(item)
    pares = []
    for dia in sorted(por_dia):
        ordenadas = sorted(por_dia[dia], key=lambda item: (item[1]["inicio"], item[1]["fin"]))
        pares.extend(zip(ordenadas, ordenadas[1:]))
    return pares


def _caminata(instancia: Instancia, origen: str, destino: str) -> int:
    if origen == destino:
        return 0
    return instancia.traslados.get((origen, destino), 0)


def verificar(instancia: Instancia, estudiantes_salida: list[dict]) -> Verificacion:
    v = Verificacion()
    agregar = v.violaciones.append
    inscritos: Counter[str] = Counter()
    vistos: set[str] = set()

    for res in estudiantes_salida:
        eid = res["id"]
        if eid in vistos:
            # Una fila repetida podría duplicar inscripciones sin que ninguna otra regla lo note
            agregar(Violacion("E", eid, "el estudiante aparece más de una vez en la salida"))
            continue
        vistos.add(eid)
        est = instancia.estudiantes.get(eid)
        if est is None:
            agregar(Violacion("E", eid, "el estudiante no existe en la instancia"))
            continue

        pedidas = {s.materia: s for s in est.solicitudes}
        respondidas = [r["materia"] for r in res["solicitudes"]]
        if sorted(respondidas) != sorted(pedidas):
            agregar(Violacion("E", eid, "las solicitudes de la salida no coinciden con las pedidas"))

        avisos = Counter(a["materia"] for a in res.get("avisos", []))
        secciones = []
        for r in res["solicitudes"]:
            estado, sid = r.get("estado"), r.get("seccion")
            if estado not in ESTADOS:
                agregar(Violacion("E", eid, f"estado desconocido '{estado}' en {r['materia']}"))
                continue
            if estado != "principal" and avisos[r["materia"]] != 1:
                agregar(Violacion("E", eid, f"{r['materia']} debe tener exactamente un aviso"))
            if estado == "no_inscrita":
                if sid is not None:
                    agregar(Violacion("E", eid, f"{r['materia']} no inscrita pero con sección", sid))
                continue
            seccion = instancia.secciones.get(sid)
            if seccion is None:
                agregar(Violacion("E", eid, f"la sección '{sid}' no existe", sid))
                continue
            solicitud = pedidas.get(r["materia"])
            aceptadas = {r["materia"]} if estado == "principal" else set(solicitud.sustitutas if solicitud else ())
            if seccion.materia not in aceptadas:
                agregar(Violacion("R1", eid, f"{sid} es de {seccion.materia}, que no atiende la solicitud de {r['materia']}", sid))
            secciones.append(seccion)
            inscritos[sid] += 1

        # R2: una sección por materia (también impide que una sustituta común atienda dos solicitudes)
        for materia, veces in Counter(s.materia for s in secciones).items():
            if veces > 1:
                agregar(Violacion("R2", eid, f"{materia} inscrita {veces} veces"))

        # R9: una solicitud sustituida no puede tener su materia principal inscrita
        inscritas = {s.materia for s in secciones}
        for r in res["solicitudes"]:
            if r.get("estado") == "sustituida" and r["materia"] in inscritas:
                agregar(Violacion("R9", eid, f"{r['materia']} figura como sustituida pero la principal está inscrita", r.get("seccion")))

        # R3: sin choques (se compara con diccionarios planos, no con Franja.se_cruza_con)
        planas = [
            (s.id, {"dia": ses.franja.dia, "inicio": ses.franja.inicio, "fin": ses.franja.fin, "edificio": ses.edificio})
            for s in secciones
            for ses in s.sesiones
        ]
        for (ida, a), (idb, b) in combinations(planas, 2):
            if ida != idb and _cruzan(a, b):
                agregar(Violacion("R3", eid, f"{ida} y {idb} se cruzan el {a['dia']}", idb))

        # R5: tope de créditos
        creditos = sum(instancia.materias[s.materia].creditos for s in secciones)
        if creditos > instancia.configuracion.max_creditos:
            agregar(Violacion("R5", eid, f"{creditos} créditos superan el tope de {instancia.configuracion.max_creditos}"))
        if res.get("creditos") is not None and res["creditos"] != creditos:
            agregar(Violacion("E", eid, f"créditos informados {res['creditos']} ≠ calculados {creditos}"))

        # R6: franjas obligatorias
        bloqueadas = [{"dia": f.dia, "inicio": f.inicio, "fin": f.fin} for f in est.preferencias.franjas_obligatorias]
        for sid, sesion in planas:
            if any(_cruzan(sesion, b) for b in bloqueadas):
                agregar(Violacion("R6", eid, f"{sid} cae en una franja obligatoriamente libre", sid))

        # R7: profesores vetados
        for s in secciones:
            if s.profesor in est.preferencias.vetados:
                agregar(Violacion("R7", eid, f"{s.id} es del profesor vetado {s.profesor}", s.id))

        # R8: traslado entre sesiones consecutivas del mismo día (los solapes ya son R3)
        for (ida, a), (idb, b) in _consecutivas(planas):
            libres = b["inicio"] - a["fin"]
            caminata = _caminata(instancia, a["edificio"], b["edificio"])
            if libres >= 0 and caminata > libres + MINUTOS_SALIDA_ANTICIPADA:
                agregar(
                    Violacion(
                        "R8",
                        eid,
                        f"{ida} → {idb} el {a['dia']}: {caminata} min de caminata y solo {libres + MINUTOS_SALIDA_ANTICIPADA} disponibles",
                        idb,
                    )
                )

    for eid in sorted(set(instancia.estudiantes) - vistos):
        agregar(Violacion("E", eid, "el estudiante no tiene resultado"))

    # R4: cupos
    for sid, cantidad in sorted(inscritos.items()):
        seccion = instancia.secciones.get(sid)
        if seccion and cantidad > seccion.cupo:
            agregar(Violacion("R4", "*", f"{sid} tiene {cantidad} inscritos y cupo {seccion.cupo}", sid))

    return v
