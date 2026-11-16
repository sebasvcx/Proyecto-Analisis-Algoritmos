"""N4: materias sustitutas (R9) y avisos con causa y sugerencia.

Si ninguna sección de la principal cabe, se prueban las sustitutas en el orden
de la lista. La sustituta hereda la prioridad de su solicitud y aporta 0,8.
"""

import pytest

from asignador.datos import cargar_instancia
from asignador.verificador import verificar
from tests.conftest import aviso, solicitud
from tests.constructores import estudiante, instancia, seccion, sesion


def avisos_de(salida: dict, eid: str) -> list[dict]:
    return next(e for e in salida["estudiantes"] if e["id"] == eid)["avisos"]


def test_principal_llena_y_sustituta_cabe(correr):
    """Tabla 4, N4: queda la sustituta y se avisa."""
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1), seccion("S2", "M2", sesion("M", "07:00"), profesor="P2")],
        [estudiante("e01", ("M1", 5)), estudiante("e02", ("M1", 4, ["M2"]))],
    )
    salida = correr(crudos, 4)
    r = solicitud(salida, "e02", "M1")
    assert (r["estado"], r["seccion"], r["materia_inscrita"]) == ("sustituida", "S2", "M2")
    a = aviso(salida, "e02", "M1")
    assert a["causa"] == "Cupo lleno"
    assert a["sustituta"] == "M2"
    assert salida["verificacion"]["total"] == 0


def test_principal_sin_secciones_sustituta_aporta_0_8(correr):
    """Tabla 5, caso 'Sustitución': se inscribe la sustituta, aporta 0,8 y se genera un aviso."""
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("S2", "M2", sesion("L", "07:00"))],
        [estudiante("e01", ("M1", 4, ["M2"]))],
    )
    salida = correr(crudos, 4)
    assert solicitud(salida, "e01", "M1")["estado"] == "sustituida"
    assert len(avisos_de(salida, "e01")) == 1
    assert aviso(salida, "e01", "M1")["causa"] == "Sin secciones"
    # Q = (C5, C4, C3, C2, C1): la sustituta cuenta en la prioridad de su solicitud
    assert salida["resumen"]["puntaje_lexicografico"] == [0, 0.8, 0, 0, 0]
    assert salida["resumen"]["solicitudes"]["sustituidas"] == 1
    assert salida["resumen"]["cobertura"] == 1.0


def test_una_sustituta_comun_atiende_una_sola_solicitud(correr):
    """Tabla 5, caso 'No duplicación'."""
    crudos = instancia(
        {"A1": 3, "A2": 3, "B": 3},
        [seccion("SB", "B", sesion("L", "07:00"))],
        [estudiante("e01", ("A1", 5, ["B"]), ("A2", 4, ["B"]))],
    )
    salida = correr(crudos, 4)
    assert solicitud(salida, "e01", "A1")["estado"] == "sustituida"
    assert solicitud(salida, "e01", "A2")["estado"] == "no_inscrita"
    a = aviso(salida, "e01", "A2")
    assert a["causa"] == "Sin secciones"
    # SB ya está en el horario: es la misma materia (R2) y además choca consigo misma (R3)
    assert a["causas"] == ["Sin secciones", "Materia ya inscrita", "Choque de horario"]
    assert salida["verificacion"]["total"] == 0


def test_prueba_las_sustitutas_en_orden(correr):
    crudos = instancia(
        {"M1": 3, "M2": 3, "M3": 3, "M4": 3},
        [
            seccion("S1", "M1", sesion("L", "07:00"), profesor="P1"),
            seccion("S3", "M3", sesion("L", "07:00", salon="B1-102"), profesor="P2"),
            seccion("S4", "M4", sesion("M", "07:00"), profesor="P3"),
        ],
        [estudiante("e01", ("M1", 5), ("M2", 4, ["M3", "M4"]))],
    )
    salida = correr(crudos, 4)
    r = solicitud(salida, "e01", "M2")
    assert (r["estado"], r["materia_inscrita"]) == ("sustituida", "M4")
    # El aviso explica la principal; lo que pasó con M3 no se mezcla porque sí hubo sustitución
    assert aviso(salida, "e01", "M2")["causas"] == ["Sin secciones"]


def test_si_la_principal_cabe_no_se_usa_la_sustituta(correr):
    """R9: la sustituta solo se inscribe si la principal no quedó."""
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("S1", "M1", sesion("L", "07:00")), seccion("S2", "M2", sesion("M", "07:00"))],
        [estudiante("e01", ("M1", 5, ["M2"]))],
    )
    salida = correr(crudos, 4)
    assert solicitud(salida, "e01", "M1")["estado"] == "principal"
    assert avisos_de(salida, "e01") == []
    assert "R9" in salida["corrida"]["reglas_del_nivel"]


@pytest.mark.parametrize("creditos_sustituta, sustituida", [(5, True), (6, False)])
def test_la_sustituta_cuenta_con_sus_propios_creditos(correr, creditos_sustituta, sustituida):
    materias = {"A": 5, "B": 5, "C": 5, "M": 3, "X": creditos_sustituta}
    secciones = [seccion(f"S{c}", c, sesion(d, "07:00")) for c, d in zip("ABCX", "LMXJ")]
    crudos = instancia(materias, secciones, [estudiante("e01", ("A", 5), ("B", 5), ("C", 5), ("M", 1, ["X"]))])
    salida = correr(crudos, 4)
    assert (solicitud(salida, "e01", "M")["estado"] == "sustituida") is sustituida
    if not sustituida:
        a = aviso(salida, "e01", "M")
        assert a["causa"] == "Sin secciones"
        assert "Tope de créditos" in a["causas"]
    assert salida["verificacion"]["total"] == 0


def test_ninguna_sustituta_cabe(correr):
    crudos = instancia(
        {"M1": 3, "M2": 3, "M3": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1)],
        [estudiante("e01", ("M1", 5)), estudiante("e02", ("M1", 4, ["M2", "M3"]))],
    )
    salida = correr(crudos, 4)
    assert solicitud(salida, "e02", "M1")["estado"] == "no_inscrita"
    a = aviso(salida, "e02", "M1")
    assert a["causa"] == "Cupo lleno"
    assert a["sustituta"] is None
    assert a["causas"] == ["Sin secciones", "Cupo lleno"]


def test_nivel_3_no_usa_sustitutas(correr):
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("S2", "M2", sesion("L", "07:00"))],
        [estudiante("e01", ("M1", 4, ["M2"]))],
    )
    salida = correr(crudos, 3)
    assert solicitud(salida, "e01", "M1")["estado"] == "no_inscrita"
    assert "R9" not in salida["corrida"]["reglas_del_nivel"]


# --- verificador ---------------------------------------------------------------

CRUDOS_VERIFICADOR = instancia(
    {"M1": 3, "M2": 3, "M3": 3},
    [
        seccion("S1", "M1", sesion("L", "07:00"), profesor="P1"),
        seccion("S2", "M2", sesion("M", "07:00"), profesor="P2"),
        seccion("S3", "M3", sesion("X", "07:00"), profesor="P3"),
    ],
    [estudiante("e01", ("M1", 5, ["M2"]), ("M3", 4))],
)


def respuesta(filas: list[tuple[str, str, str | None]], avisos: list[str]) -> list[dict]:
    prioridades = {"M1": 5, "M3": 4}
    return [
        {
            "id": "e01",
            "solicitudes": [{"materia": m, "prioridad": prioridades[m], "estado": e, "seccion": s} for m, e, s in filas],
            "avisos": [{"materia": m, "causa": "x", "sugerencia": ""} for m in avisos],
        }
    ]


def reglas(violaciones) -> set[str]:
    return {v.regla for v in violaciones}


def test_verificador_acepta_una_sustitucion_correcta():
    inst = cargar_instancia(CRUDOS_VERIFICADOR)
    ok = respuesta([("M1", "sustituida", "S2"), ("M3", "principal", "S3")], ["M1"])
    assert verificar(inst, ok).violaciones == []


def test_verificador_detecta_sustituta_con_la_principal_inscrita():
    """La principal M1 se coló por otra solicitud: viola R1 (sección ajena) y R9."""
    inst = cargar_instancia(CRUDOS_VERIFICADOR)
    mala = respuesta([("M1", "sustituida", "S2"), ("M3", "principal", "S1")], ["M1"])
    assert reglas(verificar(inst, mala).violaciones) == {"R1", "R9"}


def test_verificador_detecta_sustituta_no_declarada():
    inst = cargar_instancia(CRUDOS_VERIFICADOR)
    mala = respuesta([("M1", "sustituida", "S3"), ("M3", "no_inscrita", None)], ["M1", "M3"])
    assert reglas(verificar(inst, mala).violaciones) == {"R1"}


def test_verificador_exige_aviso_en_la_sustitucion():
    inst = cargar_instancia(CRUDOS_VERIFICADOR)
    mala = respuesta([("M1", "sustituida", "S2"), ("M3", "principal", "S3")], [])
    assert reglas(verificar(inst, mala).violaciones) == {"E"}
