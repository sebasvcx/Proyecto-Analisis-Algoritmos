"""N10: desempate opcional por semestre y mejora local según la Sección 5.4."""

import copy

import pytest

from asignador.algoritmo.causas import Causa
from asignador.algoritmo.voraz import diagnosticar
from asignador.corrida import ejecutar_corrida
from asignador.datos import cargar_instancia, construir_instancia
from asignador.dominio import Solicitud
from asignador.generador import Escasez, ParametrosGeneracion, generar_instancia
from asignador.metricas import puntaje
from asignador.objetivo import comparar
from tests.conftest import aviso, solicitud
from tests.constructores import estudiante, instancia, seccion, sesion

MARTES_OCUPADO = [{"dia": "M", "inicio": "07:00", "fin": "20:00", "tipo": "obligatoria"}]
LUNES_OCUPADO = [{"dia": "L", "inicio": "07:00", "fin": "20:00", "tipo": "obligatoria"}]


def dos_secciones_de_un_cupo(e02: dict, config: dict | None = None, e01: dict | None = None) -> dict:
    """S1 (lunes) y S2 (martes), cupo 1 cada una. e01 puede ir a cualquiera; e02 trabaja el martes."""
    return instancia(
        {"M1": 3, "M2": 3},
        [
            seccion("S1", "M1", sesion("L", "07:00"), profesor="P1", cupo=1),
            seccion("S2", "M1", sesion("M", "07:00"), profesor="P2", cupo=1),
            seccion("SX", "M2", sesion("J", "07:00"), profesor="P3"),
        ],
        [estudiante("e01", ("M1", 5), **(e01 or {})), e02],
        config=config,
    )


# ------------------------------------------------------------------ mejora local


def test_quien_quedo_sin_cupo_lo_obtiene_cuando_otro_se_mueve():
    """Tabla 4, N10: un estudiante que en N9 quedó sin cupo lo obtiene cuando otro se mueve a una sección equivalente."""
    crudos = dos_secciones_de_un_cupo(estudiante("e02", ("M1", 5), franjas_libres=MARTES_OCUPADO))
    inst = cargar_instancia(crudos)
    n9 = ejecutar_corrida(inst, 9)
    assert solicitud(n9, "e02", "M1")["estado"] == "no_inscrita"

    n10 = ejecutar_corrida(inst, 10)
    assert solicitud(n10, "e01", "M1")["seccion"] == "S2"
    assert solicitud(n10, "e02", "M1")["seccion"] == "S1"
    assert aviso(n10, "e02", "M1") is None
    assert n10["corrida"]["mejora"]["cambios_aceptados"] >= 1
    assert n10["verificacion"]["total"] == 0


def test_una_sustituida_pasa_a_principal():
    crudos = dos_secciones_de_un_cupo(estudiante("e02", ("M1", 5, ["M2"]), franjas_libres=MARTES_OCUPADO))
    inst = cargar_instancia(crudos)
    assert solicitud(ejecutar_corrida(inst, 9), "e02", "M1")["estado"] == "sustituida"
    n10 = ejecutar_corrida(inst, 10)
    assert solicitud(n10, "e02", "M1")["estado"] == "principal"
    assert aviso(n10, "e02", "M1") is None
    assert n10["resumen"]["solicitudes"]["sustituidas"] == 0


def test_cambia_de_seccion_si_sube_la_satisfaccion():
    """e01 quiere estar con e02, pero e02 solo puede ir al martes; el voraz ya había puesto a e01 el lunes."""
    crudos = dos_secciones_de_un_cupo(
        estudiante("e02", ("M1", 4), franjas_libres=LUNES_OCUPADO),
        e01={"social": [{"estudiante": "e02", "afinidad": 2}]},
    )
    crudos["secciones"][0]["cupo"] = crudos["secciones"][1]["cupo"] = 5
    inst = cargar_instancia(crudos)
    assert solicitud(ejecutar_corrida(inst, 9), "e01", "M1")["seccion"] == "S1"
    n10 = ejecutar_corrida(inst, 10)
    assert solicitud(n10, "e01", "M1")["seccion"] == "S2"
    assert n10["resumen"]["satisfaccion"]["promedio"] > ejecutar_corrida(inst, 9)["resumen"]["satisfaccion"]["promedio"]


def test_sin_cambios_examinados_queda_el_resultado_del_voraz():
    crudos = dos_secciones_de_un_cupo(estudiante("e02", ("M1", 5), franjas_libres=MARTES_OCUPADO), config={"max_cambios": 0})
    n10 = ejecutar_corrida(cargar_instancia(crudos), 10)
    assert solicitud(n10, "e02", "M1")["estado"] == "no_inscrita"
    assert n10["corrida"]["mejora"]["cambios_examinados"] == 0
    assert n10["corrida"]["mejora"]["limite_alcanzado"] is True
    assert aviso(n10, "e02", "M1")["causa"] == "Cupo lleno"


def test_si_una_seccion_cabia_y_no_se_tomo_el_aviso_lo_dice():
    """Sección 3.3: una alternativa válida que el algoritmo dejó pasar se informa como limitación."""
    sol = Solicitud("M1", 5)
    a = diagnosticar(sol, ["S1", "S2"], [[Causa.CUPO_LLENO], []])
    assert a.causa is Causa.LIMITACION
    assert a.causa.sugerencia == "Ejecutar de nuevo con más cambios examinados"


# ------------------------------------------------------------------ semestre


def un_cupo(semestre_activo: bool, prioridad_e02: int = 5) -> dict:
    """Ejemplo de la Sección 7.1: una sección con un cupo; e01 de segundo semestre y e02 de octavo."""
    return instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), cupo=1)],
        [estudiante("e01", ("M1", 5), semestre=2), estudiante("e02", ("M1", prioridad_e02), semestre=8)],
        config={"desempate_semestre": semestre_activo},
    )


def test_ejemplo_7_1_con_desempate_por_semestre():
    salida = ejecutar_corrida(cargar_instancia(un_cupo(True)), 10)
    assert solicitud(salida, "e02", "M1")["seccion"] == "S1"
    assert next(e for e in salida["estudiantes"] if e["id"] == "e02")["creditos"] == 3
    a = aviso(salida, "e01", "M1")
    assert a["causa"] == "Cedida por prioridad"
    assert salida["resumen"]["puntaje_lexicografico"][0] == 1
    assert salida["verificacion"]["total"] == 0


def test_ejemplo_7_1_sin_desempate_decide_el_codigo():
    salida = ejecutar_corrida(cargar_instancia(un_cupo(False)), 10)
    assert solicitud(salida, "e01", "M1")["seccion"] == "S1"
    assert aviso(salida, "e02", "M1")["causa"] == "Cupo lleno"


def test_el_desempate_por_semestre_es_solo_de_n10():
    assert solicitud(ejecutar_corrida(cargar_instancia(un_cupo(True)), 9), "e01", "M1")["seccion"] == "S1"


@pytest.mark.parametrize("activo", [True, False])
def test_el_semestre_no_desplaza_una_prioridad_5_por_una_4(activo):
    """Tabla 5, caso 'Límite del semestre'."""
    salida = ejecutar_corrida(cargar_instancia(un_cupo(activo, prioridad_e02=4)), 10)
    assert solicitud(salida, "e01", "M1")["seccion"] == "S1"
    assert aviso(salida, "e02", "M1")["causa"] == "Cupo lleno"


# ------------------------------------------------------------------ propiedades


@pytest.mark.parametrize("semilla", range(3))
@pytest.mark.parametrize("escasez", [Escasez.AJUSTADA, Escasez.ESCASA])
def test_n10_nunca_empeora_a_n9(semilla, escasez):
    crudos = generar_instancia(ParametrosGeneracion(estudiantes=80, secciones=60, semilla=semilla, escasez=escasez))
    inst, _ = construir_instancia(crudos)
    n9, n10 = ejecutar_corrida(inst, 9), ejecutar_corrida(inst, 10)
    assert n10["verificacion"]["total"] == 0
    assert comparar(puntaje(inst, n10["estudiantes"]), puntaje(inst, n9["estudiantes"])) >= 0


def test_n10_no_depende_del_orden_de_los_registros():
    crudos = generar_instancia(ParametrosGeneracion(estudiantes=60, secciones=60, semilla=7, escasez=Escasez.ESCASA))
    invertidos = copy.deepcopy(crudos)
    for entidad in ("materias", "profesores", "edificios", "traslados", "secciones", "estudiantes"):
        invertidos[entidad].reverse()

    def asignacion(c):
        salida = ejecutar_corrida(cargar_instancia(c), 10)
        return {e["id"]: [(r["materia"], r["estado"], r["seccion"]) for r in e["solicitudes"]] for e in salida["estudiantes"]}

    assert asignacion(crudos) == asignacion(invertidos)
