"""Satisfacción de preferencias (Sección 5.5 del documento de diseño).

Cada criterio vale entre 0 y 1 (mayor es mejor) o `None` si no se puede evaluar.
La satisfacción personal es el promedio de los criterios evaluables ponderado
por la importancia que les dio el estudiante.

Son funciones puras sobre los TADs: las usan las métricas para medir una salida
y, desde N5, el algoritmo para elegir entre secciones válidas.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise

from .dominio import Estudiante, Importancia, Instancia, Seccion
from .dominio.tiempo import Franja

# Mismo orden que en la Sección 5.5; las claves coinciden con "importancia" en estudiantes.json
CRITERIOS: tuple[str, ...] = ("profesores", "horario", "cercania", "huecos", "social")
PESO_POR_DEFECTO: dict[str, int] = {"profesores": 2, "horario": 2, "cercania": 2, "huecos": 1, "social": 2}
NEUTRO = 0.5
MINUTOS_SEMANA = 6 * 13 * 60  # 4.680: seis días de trece horas


# ------------------------------------------------------------------ criterios


def profesores(estudiante: Estudiante, secciones: Sequence[Seccion]) -> float | None:
    """Promedio de (afinidad + 2) / 4 en las secciones inscritas; una afinidad no declarada vale 0."""
    afinidad = estudiante.preferencias.afinidad_profesores
    if not afinidad or not secciones:
        return None
    return sum((afinidad.get(s.profesor, 0) + 2) / 4 for s in secciones) / len(secciones)


def horario(estudiante: Estudiante, secciones: Sequence[Seccion]) -> float | None:
    """Promedio, entre los tipos de franja declarados, de la proporción de minutos de clase bien ubicados.

    - preferidas: minutos de clase dentro de ellas;
    - evitadas y libres deseables: minutos de clase fuera de ellas.
    Las franjas de un mismo tipo se unen antes de medir, para no contar minutos repetidos.
    """
    clases = [ses.franja for s in secciones for ses in s.sesiones]
    total = sum(f.duracion() for f in clases)
    if total == 0:
        return None
    pref = estudiante.preferencias
    proporciones = []
    if pref.franjas_preferidas:
        proporciones.append(_minutos_dentro(clases, pref.franjas_preferidas) / total)
    if pref.franjas_evitadas:
        proporciones.append(1 - _minutos_dentro(clases, pref.franjas_evitadas) / total)
    if pref.franjas_deseables:
        proporciones.append(1 - _minutos_dentro(clases, pref.franjas_deseables) / total)
    return sum(proporciones) / len(proporciones) if proporciones else None


def cercania(instancia: Instancia, secciones: Sequence[Seccion]) -> float | None:
    """Uno menos la caminata promedio entre clases consecutivas, dividida entre el mayor traslado del campus."""
    caminatas = [instancia.caminata(a.edificio, b.edificio) for a, b in _consecutivas(secciones)]
    if not caminatas:
        return None
    mayor = max(instancia.traslados.values(), default=0)
    if mayor == 0:
        return 1.0
    return 1 - (sum(caminatas) / len(caminatas)) / mayor


def huecos(secciones: Sequence[Seccion]) -> float | None:
    """Uno menos los minutos libres entre clases del mismo día, divididos entre 4.680."""
    if not any(s.sesiones for s in secciones):
        return None
    libres = sum(max(0, b.franja.inicio - a.franja.fin) for a, b in _consecutivas(secciones))
    return 1 - libres / MINUTOS_SEMANA


def social(estudiante: Estudiante, secciones: Sequence[Seccion], secciones_de: Mapping[str, Iterable[str]]) -> float | None:
    """Afinidad positiva: 1 si comparten alguna sección. Negativa: 1 si no comparten.

    Se promedia con peso |afinidad|; las afinidades 0 se omiten.
    `secciones_de` da los identificadores de sección inscritos por cada estudiante.
    """
    opiniones = {otro: a for otro, a in estudiante.preferencias.social.items() if a != 0}
    if not opiniones:
        return None
    mias = {s.id for s in secciones}
    puntos = peso = 0
    for otro, afinidad in sorted(opiniones.items()):
        comparten = not mias.isdisjoint(secciones_de.get(otro, ()))
        puntos += abs(afinidad) * (comparten if afinidad > 0 else not comparten)
        peso += abs(afinidad)
    return puntos / peso


# ------------------------------------------------------------------ agregado


@dataclass(frozen=True)
class Criterio:
    valor: float | None  # None = no evaluable
    peso: int

    @property
    def cuenta(self) -> bool:
        """Entra al promedio: es evaluable y tiene peso positivo."""
        return self.valor is not None and self.peso > 0


@dataclass(frozen=True)
class Satisfaccion:
    criterios: dict[str, Criterio]

    @property
    def evaluable(self) -> bool:
        return any(c.cuenta for c in self.criterios.values())

    @property
    def total(self) -> float:
        usados = [c for c in self.criterios.values() if c.cuenta]
        if not usados:
            return NEUTRO
        return sum(c.valor * c.peso for c in usados) / sum(c.peso for c in usados)

    def como_dict(self) -> dict:
        return {
            "total": round(self.total, 4),
            "evaluable": self.evaluable,
            "criterios": {
                nombre: {
                    "valor": round(c.valor, 4) if c.valor is not None else NEUTRO,
                    "evaluable": c.valor is not None,
                    "peso": c.peso,
                }
                for nombre, c in self.criterios.items()
            },
        }


def peso(estudiante: Estudiante, criterio: str, *, declarado: bool = True) -> int:
    """Alta/media/baja/ninguna = 3/2/1/0; sin declarar, el peso por defecto (2; huecos 1)."""
    importancia: Importancia | None = estudiante.preferencias.importancia.get(criterio) if declarado else None
    return importancia.value if importancia is not None else PESO_POR_DEFECTO[criterio]


def calcular(
    instancia: Instancia,
    estudiante: Estudiante,
    secciones: Sequence[Seccion],
    secciones_de: Mapping[str, Iterable[str]],
    *,
    criterios: Iterable[str] = CRITERIOS,
    pesos_declarados: bool = True,
) -> Satisfaccion:
    """Satisfacción del estudiante con `secciones`.

    `criterios` y `pesos_declarados` permiten a los niveles N5–N8 usar solo lo que ya incorporan.
    """
    valores = {
        "profesores": lambda: profesores(estudiante, secciones),
        "horario": lambda: horario(estudiante, secciones),
        "cercania": lambda: cercania(instancia, secciones),
        "huecos": lambda: huecos(secciones),
        "social": lambda: social(estudiante, secciones, secciones_de),
    }
    activos = set(criterios)
    return Satisfaccion(
        {c: Criterio(valores[c](), peso(estudiante, c, declarado=pesos_declarados)) for c in CRITERIOS if c in activos}
    )


# ------------------------------------------------------------------ auxiliares


def _consecutivas(secciones: Sequence[Seccion]):
    """Pares de sesiones que quedan una detrás de otra en el mismo día."""
    por_dia: dict[str, list] = {}
    for s in secciones:
        for ses in s.sesiones:
            por_dia.setdefault(ses.franja.dia, []).append(ses)
    for dia in sorted(por_dia):
        yield from pairwise(sorted(por_dia[dia], key=lambda ses: (ses.franja.inicio, ses.franja.fin)))


def _minutos_dentro(clases: Sequence[Franja], franjas: Sequence[Franja]) -> int:
    """Minutos de las clases que caen dentro de la unión de `franjas`."""
    union = _unir(franjas)
    return sum(
        max(0, min(c.fin, u.fin) - max(c.inicio, u.inicio))
        for c in clases
        for u in union.get(c.dia, ())
    )


def _unir(franjas: Sequence[Franja]) -> dict[str, list[Franja]]:
    """Une, por día, las franjas que se solapan o se tocan."""
    por_dia: dict[str, list[Franja]] = {}
    for f in sorted(franjas):
        dia = por_dia.setdefault(f.dia, [])
        if dia and f.inicio <= dia[-1].fin:
            dia[-1] = Franja(f.dia, dia[-1].inicio, max(dia[-1].fin, f.fin))
        else:
            dia.append(f)
    return por_dia
