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


# --- Paso 13: más salidas con errores puestos a propósito (R8, R9, duplicados) ------------------

from asignador.corrida import ejecutar_corrida  # noqa: E402
from asignador.generador import Escasez, ParametrosGeneracion, generar_instancia  # noqa: E402


def _con_traslado(minutos):
    """Dos clases el lunes con una hora libre entre ellas (07–09 en A y 10–12 en B)."""
    return cargar_instancia(
        instancia(
            {"M1": 3, "M2": 3},
            [
                seccion("S1", "M1", sesion("L", "07:00", edificio="A"), profesor="P1"),
                seccion("S2", "M2", sesion("L", "10:00", edificio="B"), profesor="P2"),
            ],
            [estudiante("e01", ("M1", 5), ("M2", 5))],
            edificios=("A", "B"),
            traslados=[{"origen": "A", "destino": "B", "minutos": minutos}],
        )
    )


@pytest.mark.parametrize("minutos, viola", [(70, False), (71, True)])
def test_r8_con_una_hora_libre_hay_setenta_minutos(minutos, viola):
    ok = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 5, "principal", "S2")]))
    assert ("R8" in reglas(verificar(_con_traslado(minutos), ok))) is viola


def test_r8_no_aplica_entre_dias_distintos():
    inst = cargar_instancia(
        instancia(
            {"M1": 3, "M2": 3},
            [
                seccion("S1", "M1", sesion("L", "07:00", edificio="A"), profesor="P1"),
                seccion("S2", "M2", sesion("M", "09:00", edificio="B"), profesor="P2"),
            ],
            [estudiante("e01", ("M1", 5), ("M2", 5))],
            edificios=("A", "B"),
            traslados=[{"origen": "A", "destino": "B", "minutos": 60}],
        )
    )
    ok = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 5, "principal", "S2")]))
    assert verificar(inst, ok).violaciones == []


SUSTITUTA_COMUN = instancia(
    {"M1": 3, "M2": 3, "M3": 3},
    [seccion("S3", "M3", sesion("L", "07:00"))],
    [estudiante("e01", ("M1", 5, ["M3"]), ("M2", 4, ["M3"]))],
)


def test_una_sustituta_comun_no_atiende_dos_solicitudes():
    mala = respuesta(("e01", [("M1", 5, "sustituida", "S3"), ("M2", 4, "sustituida", "S3")]))
    assert reglas(verificar(cargar_instancia(copy.deepcopy(SUSTITUTA_COMUN)), mala)) == {"R2"}


def test_sustituta_comun_atendiendo_una_sola_solicitud_es_valida():
    ok = respuesta(("e01", [("M1", 5, "sustituida", "S3"), ("M2", 4, "no_inscrita", None)]))
    assert verificar(cargar_instancia(copy.deepcopy(SUSTITUTA_COMUN)), ok).violaciones == []


def test_misma_solicitud_dos_veces_en_la_salida(inst):
    mala = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M1", 5, "principal", "S1"), ("M2", 3, "no_inscrita", None)]), ("e02", [("M1", 5, "no_inscrita", None)]))
    assert {"E", "R2"} <= reglas(verificar(inst, mala))


def test_estudiante_repetido_en_la_salida(inst):
    fila = ("e02", [("M1", 5, "no_inscrita", None)])
    mala = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 3, "no_inscrita", None)]), fila, fila)
    assert reglas(verificar(inst, mala)) == {"E"}


def test_creditos_informados_incorrectos(inst):
    mala = respuesta(("e01", [("M1", 5, "principal", "S1"), ("M2", 3, "no_inscrita", None)]), ("e02", [("M1", 5, "no_inscrita", None)]))
    mala[0]["creditos"] = 6
    assert reglas(verificar(inst, mala)) == {"E"}


def test_estado_desconocido(inst):
    mala = respuesta(("e01", [("M1", 5, "inscrita", "S1"), ("M2", 3, "no_inscrita", None)]), ("e02", [("M1", 5, "no_inscrita", None)]))
    assert "E" in reglas(verificar(inst, mala))


def test_salida_real_de_n10_corrompida_llenando_una_seccion():
    """Se toma una salida válida y se mete a un estudiante más en una sección ya llena."""
    inst = cargar_instancia(generar_instancia(ParametrosGeneracion(estudiantes=80, secciones=45, semilla=5, escasez=Escasez.ESCASA)))
    salida = ejecutar_corrida(inst, 10)
    assert salida["verificacion"]["total"] == 0
    llena = next(s for s in salida["secciones"] if s["inscritos"] == s["cupo"] and s["cupo"] > 0)
    for est in salida["estudiantes"]:
        pendiente = next((r for r in est["solicitudes"] if r["materia"] == llena["materia"] and r["estado"] == "no_inscrita"), None)
        if pendiente:
            pendiente.update(estado="principal", seccion=llena["id"])
            break
    else:
        pytest.skip("ningún estudiante tenía pendiente esa materia")
    assert "R4" in reglas(verificar(inst, salida["estudiantes"]))
