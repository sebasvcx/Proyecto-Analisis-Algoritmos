"""N2: tope de créditos, franjas obligatorias y profesores vetados (R5–R7)."""

import pytest

from asignador.algoritmo import NivelNoDisponible
from asignador.corrida import ejecutar_corrida
from asignador.datos import cargar_instancia
from tests.conftest import aviso, solicitud
from tests.constructores import estudiante, instancia, seccion, sesion

TRABAJO_LUNES = [{"dia": "L", "inicio": "14:00", "fin": "20:00", "tipo": "obligatoria"}]


def test_quien_trabaja_el_lunes_no_tiene_clases_en_esa_franja(correr):
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "16:00")), seccion("S2", "M1", sesion("M", "16:00"))],
        [estudiante("e01", ("M1", 5), franjas_libres=TRABAJO_LUNES)],
    )
    salida = correr(crudos, 2)
    assert solicitud(salida, "e01", "M1")["seccion"] == "S2"
    assert salida["verificacion"]["total"] == 0


def test_todas_las_secciones_en_franja_obligatoria(correr):
    crudos = instancia({"M1": 3}, [seccion("S1", "M1", sesion("L", "16:00"))], [estudiante("e01", ("M1", 5), franjas_libres=TRABAJO_LUNES)])
    assert aviso(correr(crudos, 2), "e01", "M1")["causa"] == "Franja obligatoria"


def test_franja_deseable_no_bloquea(correr):
    deseable = [{"dia": "L", "inicio": "14:00", "fin": "20:00", "tipo": "deseable"}]
    crudos = instancia({"M1": 3}, [seccion("S1", "M1", sesion("L", "16:00"))], [estudiante("e01", ("M1", 5), franjas_libres=deseable)])
    assert solicitud(correr(crudos, 2), "e01", "M1")["estado"] == "principal"


@pytest.mark.parametrize("creditos_extra, inscrita", [(5, True), (6, False)])
def test_tope_de_20_creditos(correr, creditos_extra, inscrita):
    """Tabla 5, caso 'Créditos': 20 permitido, 21 descartado."""
    materias = {"A": 5, "B": 5, "C": 5, "X": creditos_extra}
    secciones = [seccion(f"S{c}", c, sesion(d, "07:00")) for c, d in zip("ABCX", "LMXJ")]
    crudos = instancia(materias, secciones, [estudiante("e01", ("A", 5), ("B", 5), ("C", 5), ("X", 1))])
    salida = correr(crudos, 2)
    assert (solicitud(salida, "e01", "X")["estado"] == "principal") is inscrita
    if not inscrita:
        assert aviso(salida, "e01", "X")["causa"] == "Tope de créditos"


def test_nunca_asigna_un_profesor_vetado(correr):
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1"), seccion("S2", "M1", sesion("M", "07:00"), profesor="P2")],
        [estudiante("e01", ("M1", 5), profesores=[{"id": "P1", "veto": True}])],
    )
    assert solicitud(correr(crudos, 2), "e01", "M1")["seccion"] == "S2"


def test_afinidad_negativa_no_es_veto(correr):
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1")],
        [estudiante("e01", ("M1", 5), profesores=[{"id": "P1", "afinidad": -2}])],
    )
    assert solicitud(correr(crudos, 2), "e01", "M1")["seccion"] == "S1"


def test_todas_vetadas_genera_aviso(correr):
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1")],
        [estudiante("e01", ("M1", 5), profesores=[{"id": "P1", "veto": True}])],
    )
    a = aviso(correr(crudos, 2), "e01", "M1")
    assert a["causa"] == "Profesor vetado"
    assert a["sugerencia"] == "Cambiar el veto por una afinidad negativa"


def test_causa_mas_frecuente_y_desempate_por_numero_de_regla(correr):
    """Dos secciones: una vetada, otra en franja obligatoria → empate 1-1, gana R6 sobre R7."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "16:00"), profesor="P2"), seccion("S2", "M1", sesion("M", "07:00"), profesor="P1")],
        [estudiante("e01", ("M1", 5), franjas_libres=TRABAJO_LUNES, profesores=[{"id": "P1", "veto": True}])],
    )
    a = aviso(correr(crudos, 2), "e01", "M1")
    assert a["causa"] == "Franja obligatoria"
    assert a["causas"] == ["Franja obligatoria", "Profesor vetado"]


def test_niveles_no_implementados():
    inst = cargar_instancia(instancia({}, [], []))
    with pytest.raises(NivelNoDisponible):
        ejecutar_corrida(inst, 10)
