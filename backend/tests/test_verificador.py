"""El verificador debe detectar respuestas con errores intencionales (Sección 7.3)."""

import copy

import pytest

from asignador.datos import cargar_instancia
from asignador.verificador import verificar
from tests.constructores import estudiante, instancia, seccion, sesion

CRUDOS = instancia(
    {"M1": 3, "M2": 3},
    [
        seccion("S1", "M1", sesion("L", "07:00"), profesor="P1", cupo=1),
        seccion("S2", "M2", sesion("L", "08:00", salon="X"), profesor="P2"),
    ],
    [
        estudiante("e01", ("M1", 5), ("M2", 3), profesores=[{"id": "P2", "veto": True}]),
        estudiante("e02", ("M1", 5)),
    ],
)


def respuesta(*filas):
    """filas: (estudiante, [(materia, prioridad, estado, sección)])"""
    salida = []
    for eid, solicitudes in filas:
        sols = [{"materia": m, "prioridad": p, "estado": e, "seccion": s} for m, p, e, s in solicitudes]
        avisos = [{"materia": m, "causa": "x", "sugerencia": ""} for m, _, e, _ in solicitudes if e != "principal"]
        salida.append({"id": eid, "solicitudes": sols, "avisos": avisos})
    return salida


@pytest.fixture(scope="module")
def inst():
    return cargar_instancia(copy.deepcopy(CRUDOS))


def reglas(v):
    return {x.regla for x in v.violaciones}


def test_respuesta_correcta(inst):
    ok = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 3, "no_inscrita", None)]), ("e02", [("M1", 5, "no_inscrita", None)]))
    assert verificar(inst, ok).violaciones == []


def test_exceso_de_cupo(inst):
    mala = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 3, "no_inscrita", None)]), ("e02", [("M1", 5, "principal", "S1")]))
    assert reglas(verificar(inst, mala)) == {"R4"}


def test_choque_y_profesor_vetado(inst):
    mala = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 3, "principal", "S2")]), ("e02", [("M1", 5, "no_inscrita", None)]))
    assert reglas(verificar(inst, mala)) == {"R3", "R7"}


def test_seccion_de_otra_materia(inst):
    mala = respuesta(("e01", [("M1", 5, "principal", "S2"), ("M2", 3, "no_inscrita", None)]), ("e02", [("M1", 5, "no_inscrita", None)]))
    assert "R1" in reglas(verificar(inst, mala))


def test_falta_un_estudiante_y_un_aviso(inst):
    mala = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 3, "no_inscrita", None)]))
    mala[0]["avisos"] = []
    v = verificar(inst, mala)
    assert reglas(v) == {"E"}
    assert len(v.violaciones) == 2
