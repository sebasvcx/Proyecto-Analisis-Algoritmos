from .causas import Causa
from .horario import Aviso, Contexto, Horario, Inscripcion
from .niveles import NIVELES, Nivel, NivelNoDisponible, obtener_nivel
from .mejora import mejorar
from .voraz import Asignacion, asignar_voraz


def asignar(instancia, numero_nivel: int = 1) -> Asignacion:
    """Punto de entrada único del algoritmo: ejecuta el nivel pedido."""
    nivel = obtener_nivel(numero_nivel)
    asignacion = asignar_voraz(instancia, nivel)
    if nivel.mejora:
        asignacion.mejora = mejorar(asignacion)
    return asignacion


__all__ = [
    "NIVELES",
    "Asignacion",
    "Aviso",
    "Causa",
    "Contexto",
    "Horario",
    "Inscripcion",
    "Nivel",
    "NivelNoDisponible",
    "asignar",
    "obtener_nivel",
]
