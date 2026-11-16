"""N3: tiempo de traslado entre edificios (R8).

Entre dos sesiones consecutivas del mismo día, la caminata no puede superar
los minutos libres entre ellas más los 10 de salida anticipada (Sección 5.3).
"""

import pytest

from asignador.datos import cargar_instancia
from asignador.verificador import verificar
from tests.conftest import aviso, solicitud
from tests.constructores import estudiante, instancia, seccion, sesion


def campus(minutos_a_b: int, secciones: list[dict], estudiantes: list[dict], materias: dict[str, int] | None = None) -> dict:
    """Dos edificios, A y B, a `minutos_a_b` de caminata."""
    return instancia(
        materias or {"M1": 3, "M2": 3, "M3": 3},
        secciones,
        estudiantes,
        edificios=("A", "B"),
        traslados=[{"origen": "A", "destino": "B", "minutos": minutos_a_b}],
    )


@pytest.mark.parametrize("minutos, posible", [(0, True), (8, True), (10, True), (11, False), (15, False)])
def test_clases_seguidas_en_edificios_distintos(correr, minutos, posible):
    """Tabla 4 (N3: 8 sí, 15 no) y Tabla 5, caso 'Traslado' (10 sí, 11 no)."""
    crudos = campus(
        minutos,
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "09:00", "B"))],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    salida = correr(crudos, 3)
    assert (solicitud(salida, "e01", "M2")["estado"] == "principal") is posible
    if not posible:
        a = aviso(salida, "e01", "M2")
        assert a["causa"] == "Traslado imposible"
        assert a["sugerencia"] == "Aceptar otra franja"
    assert salida["verificacion"]["total"] == 0


@pytest.mark.parametrize("minutos, posible", [(70, True), (71, False)])
def test_con_una_hora_libre_hay_setenta_minutos(correr, minutos, posible):
    crudos = campus(
        minutos,
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "10:00", "B"))],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    assert (solicitud(correr(crudos, 3), "e01", "M2")["estado"] == "principal") is posible


def test_mismo_edificio_siempre_es_posible(correr):
    crudos = campus(
        60,
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "09:00", "A", salon="A-202"))],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    assert solicitud(correr(crudos, 3), "e01", "M2")["estado"] == "principal"


def test_distinto_dia_no_es_consecutiva(correr):
    crudos = campus(
        60,
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("M", "09:00", "B"))],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    assert solicitud(correr(crudos, 3), "e01", "M2")["estado"] == "principal"


def test_toma_otra_seccion_si_el_traslado_no_alcanza(correr):
    crudos = campus(
        15,
        [
            seccion("S1", "M1", sesion("L", "07:00", "A")),
            seccion("S2a", "M2", sesion("L", "09:00", "B")),
            seccion("S2b", "M2", sesion("L", "09:00", "A", salon="A-202"), profesor="P2"),
        ],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    salida = correr(crudos, 3)
    assert solicitud(salida, "e01", "M2")["seccion"] == "S2b"
    assert salida["verificacion"]["total"] == 0


def test_revisa_tambien_la_clase_siguiente(correr):
    """La sección nueva queda entre dos clases ya inscritas: falla el traslado hacia la de después."""
    crudos = campus(
        15,
        [
            seccion("S1", "M1", sesion("L", "07:00", "B")),
            seccion("S3", "M3", sesion("L", "11:00", "A")),
            seccion("S2", "M2", sesion("L", "09:00", "B", salon="B-202")),
        ],
        [estudiante("e01", ("M1", 5), ("M3", 4), ("M2", 3))],
    )
    salida = correr(crudos, 3)
    assert solicitud(salida, "e01", "M3")["estado"] == "principal"
    assert aviso(salida, "e01", "M2")["causa"] == "Traslado imposible"


def test_una_seccion_con_dos_sesiones_seguidas_en_edificios_lejanos(correr):
    crudos = campus(
        15,
        [seccion("S1", "M1", sesion("L", "07:00", "A"), sesion("L", "09:00", "B"))],
        [estudiante("e01", ("M1", 5))],
    )
    assert aviso(correr(crudos, 3), "e01", "M1")["causa"] == "Traslado imposible"


def test_un_choque_no_se_reporta_como_traslado(correr):
    crudos = campus(
        15,
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "08:00", "B"), profesor="P2")],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    assert aviso(correr(crudos, 3), "e01", "M2")["causas"] == ["Choque de horario"]


def test_nivel_2_no_aplica_traslados_y_el_verificador_lo_detecta(correr):
    crudos = campus(
        15,
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "09:00", "B"))],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    salida = correr(crudos, 2)
    assert solicitud(salida, "e01", "M2")["estado"] == "principal"
    assert salida["verificacion"]["por_regla"]["R8"] == 1
    assert "R8" not in salida["corrida"]["reglas_del_nivel"]


def test_verificador_detecta_traslado_imposible_en_una_respuesta_manual():
    crudos = campus(
        11,
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "09:00", "B"))],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    inst = cargar_instancia(crudos)
    respuesta = [
        {
            "id": "e01",
            "solicitudes": [
                {"materia": "M1", "prioridad": 5, "estado": "principal", "seccion": "S1"},
                {"materia": "M2", "prioridad": 4, "estado": "principal", "seccion": "S2"},
            ],
            "avisos": [],
        }
    ]
    violaciones = verificar(inst, respuesta).violaciones
    assert [v.regla for v in violaciones] == ["R8"]
    assert violaciones[0].seccion == "S2"
