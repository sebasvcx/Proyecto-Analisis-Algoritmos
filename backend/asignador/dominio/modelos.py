"""Tipos abstractos de datos del problema (Sección 4 del documento de diseño).

Las entidades de entrada son inmutables. El número de inscritos de cada
sección no vive en `Seccion`: cada corrida empieza con cero inscritos, así que
la ocupación es estado de la corrida (ver `asignador.algoritmo.ocupacion`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .tiempo import Franja


@dataclass(frozen=True)
class Edificio:
    id: str
    nombre: str


@dataclass(frozen=True)
class Profesor:
    id: str
    nombre: str
    departamento: str = ""


@dataclass(frozen=True)
class Materia:
    codigo: str
    nombre: str
    creditos: int
    semestre: int


@dataclass(frozen=True)
class Sesion:
    franja: Franja
    edificio: str
    salon: str


@dataclass(frozen=True)
class Seccion:
    id: str
    materia: str
    profesor: str
    cupo: int
    sesiones: tuple[Sesion, ...]

    def choca_con(self, otra: Seccion) -> bool:
        return any(a.franja.se_cruza_con(b.franja) for a in self.sesiones for b in otra.sesiones)


@dataclass(frozen=True)
class Solicitud:
    materia: str
    prioridad: int
    sustitutas: tuple[str, ...] = ()


class Importancia(Enum):
    NINGUNA = 0
    BAJA = 1
    MEDIA = 2
    ALTA = 3


@dataclass(frozen=True)
class Preferencias:
    franjas_obligatorias: tuple[Franja, ...] = ()
    franjas_deseables: tuple[Franja, ...] = ()
    franjas_preferidas: tuple[Franja, ...] = ()
    franjas_evitadas: tuple[Franja, ...] = ()
    afinidad_profesores: dict[str, int] = field(default_factory=dict)
    vetados: frozenset[str] = frozenset()
    social: dict[str, int] = field(default_factory=dict)
    importancia: dict[str, Importancia] = field(default_factory=dict)

    def __hash__(self) -> int:  # los dict no son hashables; basta con identidad
        return id(self)


@dataclass(frozen=True)
class Estudiante:
    id: str
    nombre: str
    semestre: int
    solicitudes: tuple[Solicitud, ...] = ()
    preferencias: Preferencias = field(default_factory=Preferencias)

    def creditos_solicitados(self, materias: dict[str, Materia]) -> int:
        return sum(materias[s.materia].creditos for s in self.solicitudes)


@dataclass(frozen=True)
class Configuracion:
    max_creditos: int = 20
    valor_sustituta: float = 0.8
    desempate_semestre: bool = False
    semilla: int = 42
    max_cambios: int = 10_000


@dataclass
class Instancia:
    """Todos los datos de una ejecución, ya validados."""

    materias: dict[str, Materia]
    profesores: dict[str, Profesor]
    edificios: dict[str, Edificio]
    traslados: dict[tuple[str, str], int]
    secciones: dict[str, Seccion]
    estudiantes: dict[str, Estudiante]
    configuracion: Configuracion = field(default_factory=Configuracion)
    _por_materia: dict[str, list[Seccion]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        for seccion in sorted(self.secciones.values(), key=lambda s: s.id):
            self._por_materia.setdefault(seccion.materia, []).append(seccion)

    def secciones_de(self, materia: str) -> list[Seccion]:
        """Secciones de una materia, ordenadas por identificador."""
        return self._por_materia.get(materia, [])

    def caminata(self, origen: str, destino: str) -> int:
        if origen == destino:
            return 0
        return self.traslados[(origen, destino)]
