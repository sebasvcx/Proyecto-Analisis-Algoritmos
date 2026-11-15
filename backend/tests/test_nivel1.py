"""N1: prioridad, choques y cupos (R1–R4)."""

import random

from tests.conftest import aviso, solicitud
from tests.constructores import estudiante, instancia, seccion, sesion


def test_con_cupo_uno_gana_la_mayor_prioridad(correr):
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1)],
        [estudiante("e01", ("M1", 2)), estudiante("e02", ("M1", 5))],
    )
    salida = correr(crudos, 1)
    assert solicitud(salida, "e02", "M1")["seccion"] == "S1"
    assert solicitud(salida, "e01", "M1")["estado"] == "no_inscrita"
    assert aviso(salida, "e01", "M1")["causa"] == "Cupo lleno"


def test_ejemplo_del_documento_sin_desempate_por_semestre(correr):
    """Sección 7.1: con el desempate desactivado, decide el código (e01)."""
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1)],
        [estudiante("e02", ("M1", 5), semestre=8), estudiante("e01", ("M1", 5), semestre=2)],
    )
    salida = correr(crudos, 1)
    assert solicitud(salida, "e01", "M1")["seccion"] == "S1"
    assert salida["estudiantes"][0]["creditos"] == 3
    assert solicitud(salida, "e02", "M1")["estado"] == "no_inscrita"
    assert salida["resumen"]["puntaje_lexicografico"] == [1.0, 0, 0, 0, 0]
    assert salida["verificacion"]["total"] == 0


def test_prioridad_5_se_prefiere_a_dos_de_prioridad_1(correr):
    """Tabla 5, caso 'Prioridades'."""
    crudos = instancia(
        {"M1": 3, "M2": 2, "M3": 2},
        [
            seccion("S1", "M1", sesion("L", "07:00"), sesion("X", "07:00"), profesor="P1"),
            seccion("S2", "M2", sesion("L", "07:00", salon="X"), profesor="P2", cupo=5),
            seccion("S3", "M3", sesion("X", "07:00", salon="Y"), profesor="P3", cupo=5),
        ],
        [estudiante("e01", ("M2", 1), ("M3", 1), ("M1", 5))],
    )
    salida = correr(crudos, 1)
    assert solicitud(salida, "e01", "M1")["estado"] == "principal"
    assert aviso(salida, "e01", "M2")["causa"] == "Choque de horario"


def test_toma_la_siguiente_seccion_si_la_primera_choca(correr):
    crudos = instancia(
        {"M1": 3, "M2": 3},
        [
            seccion("A1", "M1", sesion("L", "07:00"), profesor="P1"),
            seccion("B1", "M2", sesion("L", "08:00", salon="X"), profesor="P2"),
            seccion("B2", "M2", sesion("L", "09:00", salon="Y"), profesor="P3"),
        ],
        [estudiante("e01", ("M1", 5), ("M2", 4))],
    )
    salida = correr(crudos, 1)
    assert solicitud(salida, "e01", "M2")["seccion"] == "B2"  # 07-09 y 09-11 no se cruzan


def test_estudiante_sin_solicitudes(correr):
    crudos = instancia({"M1": 3}, [seccion("S1", "M1", sesion("L", "07:00"))], [estudiante("e01")])
    est = correr(crudos, 1)["estudiantes"][0]
    assert est["solicitudes"] == [] and est["avisos"] == [] and est["creditos"] == 0


def test_materia_sin_secciones_genera_aviso(correr):
    crudos = instancia({"M1": 3, "M2": 3}, [seccion("S1", "M1", sesion("L", "07:00"))], [estudiante("e01", ("M2", 3))])
    salida = correr(crudos, 1)
    assert aviso(salida, "e01", "M2")["causa"] == "Sin secciones"


def test_reordenar_registros_no_cambia_el_resultado(correr):
    estudiantes = [estudiante(f"e{i:02d}", ("M1", 1 + i % 5), ("M2", 5 - i % 5)) for i in range(12)]
    secciones = [
        seccion("S1", "M1", sesion("L", "07:00"), profesor="P1", cupo=4),
        seccion("S2", "M1", sesion("M", "07:00"), profesor="P1", cupo=4),
        seccion("S3", "M2", sesion("L", "07:00", salon="X"), profesor="P2", cupo=5),
    ]
    original = correr(instancia({"M1": 3, "M2": 3}, secciones, estudiantes), 1)
    random.Random(7).shuffle(estudiantes)
    random.Random(7).shuffle(secciones)
    mezclado = correr(instancia({"M1": 3, "M2": 3}, secciones, estudiantes), 1)
    assert original["estudiantes"] == mezclado["estudiantes"]


def test_nivel_1_no_aplica_franjas_obligatorias(correr):
    """N1 es un nivel de prueba: el verificador informa la violación de R6."""
    libres = [{"dia": "L", "inicio": "14:00", "fin": "20:00", "tipo": "obligatoria"}]
    crudos = instancia({"M1": 3}, [seccion("S1", "M1", sesion("L", "16:00"))], [estudiante("e01", ("M1", 5), franjas_libres=libres)])
    salida = correr(crudos, 1)
    assert solicitud(salida, "e01", "M1")["estado"] == "principal"
    assert salida["verificacion"]["por_regla"]["R6"] == 1
