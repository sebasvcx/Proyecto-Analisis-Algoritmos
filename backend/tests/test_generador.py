import pytest

from asignador.corrida import ejecutar_corrida
from asignador.datos import construir_instancia
from asignador.generador import Escasez, ParametrosGeneracion, generar_instancia


def test_misma_semilla_mismos_datos():
    p = ParametrosGeneracion(estudiantes=40, semilla=3)
    assert generar_instancia(p) == generar_instancia(p)


def test_semillas_distintas_dan_datos_distintos():
    assert generar_instancia(ParametrosGeneracion(estudiantes=40, semilla=1)) != generar_instancia(ParametrosGeneracion(estudiantes=40, semilla=2))


@pytest.mark.parametrize("semilla", range(5))
@pytest.mark.parametrize("escasez", list(Escasez))
def test_instancias_generadas_son_validas_y_nivel_2_no_viola_reglas(semilla, escasez):
    crudos = generar_instancia(ParametrosGeneracion(estudiantes=120, secciones=60, semilla=semilla, escasez=escasez))
    inst, reporte = construir_instancia(crudos)
    assert reporte.es_valido, [str(p) for p in reporte.errores]
    assert len(crudos["secciones"]) == 60
    salida = ejecutar_corrida(inst, 2)
    assert salida["verificacion"]["total"] == 0


def test_escasez_reduce_la_cobertura():
    def cobertura(escasez):
        crudos = generar_instancia(ParametrosGeneracion(estudiantes=200, semilla=0, escasez=escasez))
        inst, _ = construir_instancia(crudos)
        return ejecutar_corrida(inst, 2)["resumen"]["cobertura"]

    assert cobertura(Escasez.HOLGADA) > cobertura(Escasez.ESCASA)
