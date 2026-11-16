"""Solución exacta por búsqueda exhaustiva y comparación con N10 (Sección 7.1)."""

import pytest

from asignador.comparacion_exacta import comparar_con_optimo, resumen_de_casos
from asignador.datos import cargar_instancia
from asignador.exacto import InstanciaDemasiadoGrande, a_salida, resolver
from asignador.generador.pequenos import generar_pequena
from asignador.verificador import verificar
from tests.constructores import estudiante, instancia, seccion, sesion


def asignado(optimo, eid: str, materia: str) -> str | None:
    return next(r.seccion for r in optimo.registros if r.estudiante == eid and r.materia == materia)


# ------------------------------------------------------------------ casos con respuesta conocida


@pytest.mark.parametrize("semestre_activo, gana", [(True, "e02"), (False, "e01")])
def test_ejemplo_de_la_seccion_7_1(semestre_activo, gana):
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1)],
        [estudiante("e01", ("M1", 5), semestre=2), estudiante("e02", ("M1", 5), semestre=8)],
        config={"desempate_semestre": semestre_activo},
    )
    optimo = resolver(cargar_instancia(crudos))
    assert asignado(optimo, gana, "M1") == "S1"
    assert optimo.puntaje.c == (1, 0, 0, 0, 0)


def test_prefiere_una_de_prioridad_5_a_dos_de_prioridad_1():
    crudos = instancia(
        {"A": 3, "B": 3, "C": 3},
        [
            seccion("SA", "A", sesion("L", "07:00"), profesor="P1"),
            seccion("SB", "B", sesion("L", "07:00", salon="B1-102"), profesor="P2"),
            seccion("SC", "C", sesion("L", "07:00", salon="B1-103"), profesor="P3"),
        ],
        [estudiante("e01", ("A", 5), ("B", 1), ("C", 1))],
    )
    optimo = resolver(cargar_instancia(crudos))
    assert asignado(optimo, "e01", "A") == "SA"
    assert optimo.puntaje.c == (1, 0, 0, 0, 0)


def test_encuentra_la_reubicacion_del_ejemplo_n10():
    """Tabla 4, N10: el óptimo inscribe a los dos estudiantes."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1", cupo=1), seccion("S2", "M1", sesion("M", "07:00"), profesor="P2", cupo=1)],
        [
            estudiante("e01", ("M1", 5)),
            estudiante("e02", ("M1", 5), franjas_libres=[{"dia": "M", "inicio": "07:00", "fin": "20:00", "tipo": "obligatoria"}]),
        ],
    )
    optimo = resolver(cargar_instancia(crudos))
    assert (asignado(optimo, "e01", "M1"), asignado(optimo, "e02", "M1")) == ("S2", "S1")


def test_respeta_el_traslado_entre_edificios():
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("S1", "M1", sesion("L", "07:00", "A"), profesor="P1"), seccion("S2", "M2", sesion("L", "09:00", "B"), profesor="P2")],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
        edificios=("A", "B"),
        traslados=[{"origen": "A", "destino": "B", "minutos": 11}],
    )
    optimo = resolver(cargar_instancia(crudos))
    assert asignado(optimo, "e01", "M2") is None


# ------------------------------------------------------------------ propiedades en instancias generadas


@pytest.mark.parametrize("semilla", range(40))
def test_la_solucion_exacta_cumple_todas_las_reglas(semilla):
    inst = cargar_instancia(generar_pequena(semilla))
    optimo = resolver(inst)
    assert verificar(inst, a_salida(inst, optimo.registros)).violaciones == []


@pytest.mark.parametrize("semilla", range(40))
def test_la_poda_no_cambia_el_optimo(semilla):
    inst = cargar_instancia(generar_pequena(semilla, desempate_semestre=semilla % 2 == 0))
    con_poda, sin_poda = resolver(inst), resolver(inst, podar=False)
    assert con_poda.puntaje == sin_poda.puntaje
    assert con_poda.nodos <= sin_poda.nodos


def test_n10_nunca_supera_al_optimo():
    """`comparar_con_optimo` falla si N10 le gana al óptimo o si su salida es inválida."""
    for semestre in (False, True):
        r = resumen_de_casos(range(60), desempate_semestre=semestre)
        assert r["optimo"] + r["empate"] + r["peor"] == 60
        assert r["porcentaje_igual_de_bueno"] >= 50


def test_resultado_identico_cuenta_como_optimo():
    """Regresión: la satisfacción redondeada de la salida hacía parecer a N10 mejor que el óptimo (semilla 11)."""
    assert comparar_con_optimo(cargar_instancia(generar_pequena(11))).resultado == "optimo"


def test_las_instancias_pequenas_respetan_los_tamanos_de_la_seccion_7_3():
    for semilla in range(100):
        crudos = generar_pequena(semilla)
        inst = cargar_instancia(crudos)  # falla si los datos no son válidos
        assert 2 <= len(inst.estudiantes) <= 6
        assert all(1 <= len(e.solicitudes) <= 3 for e in inst.estudiantes.values())
        assert all(1 <= len(inst.secciones_de(m)) <= 2 for m in inst.materias)


def test_limite_de_nodos():
    with pytest.raises(InstanciaDemasiadoGrande):
        resolver(cargar_instancia(generar_pequena(0)), max_nodos=1)
