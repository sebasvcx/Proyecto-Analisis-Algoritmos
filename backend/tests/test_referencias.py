"""Paso 11: asignaciones de referencia (Sección 7.3): aleatoria válida y por orden de llegada."""

import random

import pytest

from asignador.datos import cargar_instancia
from asignador.generador import Escasez, ParametrosGeneracion, generar_instancia
from asignador.referencias import Referencia, ejecutar_referencia
from tests.conftest import solicitud
from tests.constructores import estudiante, instancia, seccion, sesion


def correr(crudos, tipo, semilla=0):
    return ejecutar_referencia(cargar_instancia(crudos), tipo, semilla)


def test_llegada_atiende_por_orden_del_archivo_no_por_prioridad():
    """Con un cupo, gana quien llegó primero aunque pida la materia con menor prioridad."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1)],
        [estudiante("e02", ("M1", 1)), estudiante("e01", ("M1", 5))],
    )
    salida = correr(crudos, "llegada")
    assert solicitud(salida, "e02", "M1")["estado"] == "principal"
    assert solicitud(salida, "e01", "M1")["estado"] == "no_inscrita"
    assert salida["verificacion"]["total"] == 0


def test_llegada_dentro_del_estudiante_va_de_mayor_a_menor_prioridad():
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("A", "M1", sesion("L", "07:00"), profesor="P1"), seccion("B", "M2", sesion("L", "08:00", salon="X"), profesor="P2")],
        [estudiante("e01", ("M1", 1), ("M2", 5))],
    )
    salida = correr(crudos, "llegada")
    assert solicitud(salida, "e01", "M2")["estado"] == "principal"
    assert solicitud(salida, "e01", "M1")["estado"] == "no_inscrita"


def test_referencias_usan_sustitutas():
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("S2", "M2", sesion("L", "07:00"))],
        [estudiante("e01", ("M1", 5, ["M2"]))],
    )
    for tipo in Referencia:
        salida = correr(crudos, tipo)
        assert solicitud(salida, "e01", "M1")["estado"] == "sustituida"
        assert salida["verificacion"]["total"] == 0


def test_aleatoria_es_reproducible_con_la_misma_semilla():
    crudos = generar_instancia(ParametrosGeneracion(estudiantes=60, secciones=50, semilla=3))
    a, b = correr(crudos, "aleatoria", 7), correr(crudos, "aleatoria", 7)
    assert a["estudiantes"] == b["estudiantes"]
    assert a["estudiantes"] != correr(crudos, "aleatoria", 8)["estudiantes"]


def test_llegada_depende_del_orden_del_archivo():
    """A diferencia del algoritmo, la referencia por llegada sí cambia si se reordena el archivo."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1)],
        [estudiante("e01", ("M1", 5)), estudiante("e02", ("M1", 5))],
    )
    primero = correr(crudos, "llegada")
    crudos["estudiantes"].reverse()
    segundo = correr(crudos, "llegada")
    assert solicitud(primero, "e01", "M1")["estado"] == "principal"
    assert solicitud(segundo, "e02", "M1")["estado"] == "principal"


@pytest.mark.parametrize("escasez", list(Escasez))
@pytest.mark.parametrize("tipo", list(Referencia))
def test_referencias_siempre_validas(escasez, tipo):
    crudos = generar_instancia(ParametrosGeneracion(estudiantes=150, secciones=60, semilla=1, escasez=escasez))
    salida = correr(crudos, tipo, semilla=random.Random(escasez.value).randint(0, 99))
    assert salida["verificacion"]["total"] == 0, salida["verificacion"]["por_regla"]
    assert salida["corrida"]["referencia"] == tipo.value


def test_n10_nunca_es_peor_que_las_referencias_en_prioridad_5():
    from asignador.corrida import ejecutar_corrida

    crudos = generar_instancia(ParametrosGeneracion(estudiantes=150, secciones=60, semilla=2, escasez=Escasez.ESCASA))
    inst = cargar_instancia(crudos)
    c5_n10 = ejecutar_corrida(inst, 10)["resumen"]["puntaje_lexicografico"][0]
    for tipo in Referencia:
        assert c5_n10 >= ejecutar_referencia(inst, tipo, 0)["resumen"]["puntaje_lexicografico"][0]
