"""Paso 9: casos con respuesta conocida (Sección 7.1, tipo 2)."""

from collections import Counter

import pytest

from asignador.comparacion_conocida import comparar_con_conocido
from asignador.datos import construir_instancia
from asignador.generador.conocidos import generar_conocido
from asignador.metricas import calcular_metricas
from asignador.verificador import verificar


@pytest.mark.parametrize("semilla", range(25))
def test_la_respuesta_plantada_es_valida_y_atiende_todo(semilla):
    caso = generar_conocido(semilla)
    instancia, reporte = construir_instancia(caso.crudos)
    assert reporte.es_valido, [str(p) for p in reporte.errores]
    referencia = caso.salida_de_referencia()
    assert verificar(instancia, referencia).violaciones == []
    assert calcular_metricas(instancia, referencia)["cobertura"] == 1.0


def test_misma_semilla_mismo_caso():
    assert generar_conocido(3).crudos == generar_conocido(3).crudos


def test_los_cupos_plantados_son_justos():
    """Toda sección usada en la respuesta tiene exactamente el cupo que necesita."""
    caso = generar_conocido(11, estudiantes=40)
    usos = Counter(sid for horario in caso.respuesta.values() for sid in horario.values())
    for s in caso.crudos["secciones"]:
        assert s["cupo"] == (usos[s["id"]] or 1)


@pytest.mark.parametrize("semilla", range(10))
def test_el_algoritmo_nunca_supera_a_la_respuesta_en_c(semilla):
    """La respuesta atiende todo, así que su C es el máximo: lo que falta nunca es negativo."""
    comparacion = comparar_con_conocido(generar_conocido(semilla), nivel=10)
    assert comparacion.referencia_valida
    assert all(f >= 0 for f in comparacion.faltantes_por_prioridad)


def test_solo_se_compara_desde_n3():
    with pytest.raises(ValueError):
        comparar_con_conocido(generar_conocido(0), nivel=2)
