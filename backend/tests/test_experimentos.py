"""Paso 12: experimentos (Sección 7.3)."""

import pytest

from asignador.experimentos import Plan, ejecutar, ejecutar_metodo, resumir, secciones_para
from asignador.generador import Escasez

PLAN = Plan(tamanos=(20, 40), escaseces=(Escasez.HOLGADA, Escasez.ESCASA), semillas=(0, 1, 2), metodos=("aleatoria", "llegada", "N4", "N10"))


@pytest.fixture(scope="module")
def filas():
    return list(ejecutar(PLAN))


def test_una_fila_por_combinacion(filas):
    assert len(filas) == PLAN.total == 2 * 2 * 3 * 4


def test_ninguna_corrida_viola_reglas(filas):
    assert all(f["violaciones"] == 0 for f in filas)


def test_resumen_con_mediana_y_rango(filas):
    resumen = resumir(filas)
    assert len(resumen) == 2 * 2 * 4
    for r in resumen:
        assert r["semillas"] == 3
        assert r["cobertura_min"] <= r["cobertura_mediana"] <= r["cobertura_max"]


def test_n10_nunca_peor_que_las_referencias_en_prioridad_5(filas):
    por_instancia = {}
    for f in filas:
        por_instancia.setdefault((f["estudiantes"], f["escasez"], f["semilla"]), {})[f["metodo"]] = f
    for metodos in por_instancia.values():
        assert metodos["N10"]["c5"] >= metodos["aleatoria"]["c5"]
        assert metodos["N10"]["c5"] >= metodos["llegada"]["c5"]


def test_secciones_crecen_con_los_estudiantes():
    assert secciones_para(20) == 42  # mínimo: una por materia del catálogo
    assert secciones_para(250) == 96
    assert secciones_para(2000) == 768


def test_metodo_desconocido():
    with pytest.raises(ValueError):
        ejecutar_metodo(None, "voraz", 0)
