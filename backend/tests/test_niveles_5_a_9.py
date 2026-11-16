"""N5–N9: entre las secciones válidas se elige la que más satisface (Tabla 4).

Cada nivel agrega criterios: N5 profesores; N6 horario y huecos; N7 cercanía;
N8 importancia declarada; N9 compañeros. Una comodidad nunca justifica perder
una materia (Sección 5.4; Tabla 5, caso "Preferencias").
"""

import pytest

from tests.conftest import solicitud
from tests.constructores import estudiante, instancia, seccion, sesion

MANANA = [{"dia": "*", "inicio": "07:00", "fin": "13:00"}]


def seccion_de(salida: dict, eid: str, materia: str) -> str | None:
    return solicitud(salida, eid, materia)["seccion"]


# ------------------------------------------------------------------ N5 profesores


def test_n5_elige_el_profesor_con_mayor_afinidad(correr):
    """Tabla 4: entre profesores con afinidad +2 y −1, elige el de +2."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1"), seccion("S2", "M1", sesion("M", "07:00"), profesor="P2")],
        [estudiante("e01", ("M1", 5), profesores=[{"id": "P1", "afinidad": -1}, {"id": "P2", "afinidad": 2}])],
    )
    assert seccion_de(correr(crudos, 4), "e01", "M1") == "S1"
    salida = correr(crudos, 5)
    assert seccion_de(salida, "e01", "M1") == "S2"
    assert salida["verificacion"]["total"] == 0


def test_n5_sin_preferencias_toma_la_de_menor_identificador(correr):
    crudos = instancia(
        {"M1": 3},
        [seccion("S2", "M1", sesion("L", "07:00"), profesor="P1"), seccion("S1", "M1", sesion("M", "07:00"), profesor="P2")],
        [estudiante("e01", ("M1", 5))],
    )
    assert seccion_de(correr(crudos, 5), "e01", "M1") == "S1"


def test_el_profesor_preferido_no_hace_perder_una_materia_de_prioridad_5(correr):
    """Tabla 5, caso 'Preferencias': se conserva la mayor atención de prioridad 5."""
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [
            seccion("S1", "M1", sesion("M", "07:00"), profesor="P1"),
            seccion("S2", "M1", sesion("L", "07:00", salon="B1-102"), profesor="P2"),
            seccion("S3", "M2", sesion("L", "07:00"), profesor="P3"),
        ],
        [estudiante("e01", ("M1", 5), ("M2", 5), profesores=[{"id": "P2", "afinidad": 2}])],
    )
    salida = correr(crudos, 9)
    assert seccion_de(salida, "e01", "M1") == "S1"
    assert solicitud(salida, "e01", "M2")["estado"] == "principal"
    assert salida["resumen"]["puntaje_lexicografico"][0] == 2


def test_tampoco_se_pierde_una_materia_de_menor_prioridad_por_comodidad(correr):
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [
            seccion("S1", "M1", sesion("M", "07:00"), profesor="P1"),
            seccion("S2", "M1", sesion("L", "07:00", salon="B1-102"), profesor="P2"),
            seccion("S3", "M2", sesion("L", "07:00"), profesor="P3"),
        ],
        [estudiante("e01", ("M1", 5), ("M2", 1), profesores=[{"id": "P2", "afinidad": 2}])],
    )
    salida = correr(crudos, 9)
    assert solicitud(salida, "e01", "M2")["estado"] == "principal"


# ------------------------------------------------------------------ N6 horario y huecos


def test_n6_quien_prefiere_mananas_queda_a_las_7(correr):
    """Tabla 4: queda en la sección de las 7:00 y no en la de las 18:00."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "18:00"), profesor="P1"), seccion("S2", "M1", sesion("L", "07:00"), profesor="P2")],
        [estudiante("e01", ("M1", 5), franjas_preferidas=MANANA)],
    )
    assert seccion_de(correr(crudos, 5), "e01", "M1") == "S1"
    assert seccion_de(correr(crudos, 6), "e01", "M1") == "S2"


def test_n6_evita_huecos(correr):
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [
            seccion("S1", "M1", sesion("L", "07:00"), profesor="P1"),
            seccion("S2", "M2", sesion("L", "16:00"), profesor="P2"),
            seccion("S3", "M2", sesion("L", "09:00"), profesor="P3"),
        ],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    assert seccion_de(correr(crudos, 5), "e01", "M2") == "S2"
    assert seccion_de(correr(crudos, 6), "e01", "M2") == "S3"


# ------------------------------------------------------------------ N7 cercanía


def test_n7_elige_el_edificio_mas_cercano_a_la_clase_anterior(correr):
    """Tabla 4: con dos secciones iguales, elige la del edificio más cercano."""
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [
            seccion("S1", "M1", sesion("L", "07:00", "A"), profesor="P1"),
            seccion("S2", "M2", sesion("L", "11:00", "C"), profesor="P2"),
            seccion("S3", "M2", sesion("L", "11:00", "B"), profesor="P3"),
        ],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
        edificios=("A", "B", "C"),
        traslados=[
            {"origen": "A", "destino": "B", "minutos": 5},
            {"origen": "A", "destino": "C", "minutos": 9},
            {"origen": "B", "destino": "C", "minutos": 6},
        ],
    )
    assert seccion_de(correr(crudos, 6), "e01", "M2") == "S2"
    assert seccion_de(correr(crudos, 7), "e01", "M2") == "S3"


# ------------------------------------------------------------------ N8 importancia


def caso_importancia(profesores: str, horario: str) -> dict:
    # S1: profesor favorito (+2) a las 18:00; S2: profesor con afinidad −2 a las 7:00
    return instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "18:00"), profesor="P1"), seccion("S2", "M1", sesion("L", "07:00"), profesor="P2")],
        [
            estudiante(
                "e01",
                ("M1", 5),
                franjas_preferidas=MANANA,
                profesores=[{"id": "P1", "afinidad": 2}, {"id": "P2", "afinidad": -2}],
                importancia={"profesores": profesores, "horario": horario},
            )
        ],
    )


@pytest.mark.parametrize("profesores, horario, esperada", [("alta", "baja", "S1"), ("baja", "alta", "S2")])
def test_n8_invertir_la_importancia_cambia_la_seccion(correr, profesores, horario, esperada):
    """Tabla 4: invertir la importancia de profesores y horario cambia la sección elegida."""
    crudos = caso_importancia(profesores, horario)
    assert seccion_de(correr(crudos, 8), "e01", "M1") == esperada
    # N7 usa los pesos por defecto: empatan y queda la de menor identificador
    assert seccion_de(correr(crudos, 7), "e01", "M1") == "S1"


def test_n8_importancia_ninguna_ignora_el_criterio(correr):
    crudos = caso_importancia("ninguna", "baja")
    assert seccion_de(correr(crudos, 8), "e01", "M1") == "S2"


# ------------------------------------------------------------------ N9 compañeros


def caso_social(**preferencias_por_estudiante) -> dict:
    """e01 tiene M0 el lunes a las 7, así que su M1 queda en S2 (martes).

    `preferencias_por_estudiante`: e01=..., e02=... con las preferencias de cada uno.
    """
    return instancia(
        {"M0": 3, "M1": 3},
        [
            seccion("S0", "M0", sesion("L", "07:00"), profesor="P1"),
            seccion("S1", "M1", sesion("L", "07:00", salon="B1-102"), profesor="P2"),
            seccion("S2", "M1", sesion("M", "07:00"), profesor="P3"),
        ],
        [
            estudiante("e01", ("M0", 5), ("M1", 4), **preferencias_por_estudiante.get("e01", {})),
            estudiante("e02", ("M1", 4), **preferencias_por_estudiante.get("e02", {})),
        ],
    )


def test_n9_se_favorece_compartir_seccion_con_un_amigo(correr):
    """Tabla 4: si se atienden las mismas materias, se favorece compartir sección."""
    crudos = caso_social(e02={"social": [{"estudiante": "e01", "afinidad": 2}]})
    assert seccion_de(correr(crudos, 8), "e02", "M1") == "S1"
    salida = correr(crudos, 9)
    assert seccion_de(salida, "e01", "M1") == "S2"
    assert seccion_de(salida, "e02", "M1") == "S2"
    assert salida["verificacion"]["total"] == 0


def test_n9_cuenta_la_satisfaccion_de_quien_declaro_la_amistad(correr):
    """Solo e01 declara la amistad; e02 elige S2 porque eso sube la satisfacción de e01."""
    crudos = caso_social(e01={"social": [{"estudiante": "e02", "afinidad": 2}]})
    assert seccion_de(correr(crudos, 9), "e02", "M1") == "S2"


def test_n9_evitar_a_alguien_cambia_la_eleccion(correr):
    """Sin M0, e01 queda en S1 (menor identificador); e02, que quiere evitarlo, pasa a S2."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P2"), seccion("S2", "M1", sesion("M", "07:00"), profesor="P3")],
        [estudiante("e01", ("M1", 4)), estudiante("e02", ("M1", 4), social=[{"estudiante": "e01", "afinidad": -2}])],
    )
    assert seccion_de(correr(crudos, 8), "e02", "M1") == "S1"
    assert seccion_de(correr(crudos, 9), "e02", "M1") == "S2"


# ------------------------------------------------------------------ todos los niveles


@pytest.mark.parametrize("nivel", range(5, 10))
def test_niveles_5_a_9_cubren_r1_a_r9(correr, nivel):
    salida = correr(instancia({}, [], [estudiante("e01")]), nivel)
    assert salida["corrida"]["reglas_del_nivel"] == ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"]
