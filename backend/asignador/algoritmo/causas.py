"""Causas de no inscripción (Tabla 3 del documento de diseño)."""

from __future__ import annotations

from enum import Enum


class Causa(Enum):
    # (orden de desempate = número de regla, texto, sugerencia)
    SIN_SECCIONES = (0, "Sin secciones", "Revisar el código de la materia")
    MATERIA_YA_INSCRITA = (2, "Materia ya inscrita", "Revisar sustitutas repetidas entre solicitudes")
    CHOQUE_HORARIO = (3, "Choque de horario", "Revisar secciones y prioridades declaradas")
    CUPO_LLENO = (4, "Cupo lleno", "Revisar alternativas y oferta de cupos")
    TOPE_CREDITOS = (5, "Tope de créditos", "Quitar una materia de menor prioridad")
    FRANJA_OBLIGATORIA = (6, "Franja obligatoria", "Revisar las franjas obligatorias")
    PROFESOR_VETADO = (7, "Profesor vetado", "Cambiar el veto por una afinidad negativa")
    TRASLADO_IMPOSIBLE = (8, "Traslado imposible", "Aceptar otra franja")
    CEDIDA_POR_PRIORIDAD = (10, "Cedida por prioridad", "")
    # Sección 3.3: si el algoritmo dejó pasar una alternativa válida, se indica como limitación
    LIMITACION = (11, "Limitación del algoritmo", "Ejecutar de nuevo con más cambios examinados")

    @property
    def regla(self) -> int:
        return self.value[0]

    @property
    def texto(self) -> str:
        return self.value[1]

    @property
    def sugerencia(self) -> str:
        return self.value[2]
