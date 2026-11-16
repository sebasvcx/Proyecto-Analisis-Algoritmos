"""Cómo comparar resultados (Sección 5.4) y su cálculo desde la salida."""

from asignador.datos import cargar_instancia
from asignador.objetivo import Registro, comparar, criterio_decisivo, puntuar
from tests.constructores import estudiante, instancia, seccion, sesion


def preparar(materias: dict[str, int], estudiantes: list[dict], *, semestre: bool = False, secciones: list[dict] | None = None):
    return cargar_instancia(instancia(materias, secciones or [], estudiantes, config={"desempate_semestre": semestre}))


def mejor(inst, a: list[Registro], b: list[Registro], sat_a: float = 0, sat_b: float = 0) -> tuple[str, str | None]:
    """('A' | 'B' | '=', criterio que decidió)."""
    pa, pb = puntuar(inst, a, sat_a), puntuar(inst, b, sat_b)
    return {1: "A", -1: "B", 0: "="}[comparar(pa, pb)], criterio_decisivo(pa, pb)


def test_una_de_prioridad_5_vale_mas_que_dos_de_prioridad_1():
    """Tabla 5, caso 'Prioridades'."""
    inst = preparar({"M5": 3, "Ma": 3, "Mb": 3}, [estudiante("e01", ("M5", 5), ("Ma", 1), ("Mb", 1))])
    a = [Registro("e01", "M5", "S5"), Registro("e01", "Ma", None), Registro("e01", "Mb", None)]
    b = [Registro("e01", "M5", None), Registro("e01", "Ma", "Sa"), Registro("e01", "Mb", "Sb")]
    assert mejor(inst, a, b) == ("A", "C")


def test_cinco_sustituciones_equivalen_a_cuatro_principales():
    """Sección 5.4: dentro de una prioridad, 5 × 0,8 = 4 × 1. Desempata la suma de posiciones."""
    codigos = [f"M{i}" for i in range(5)]
    materias = {c: 1 for c in codigos} | {f"X{i}": 1 for i in range(5)}
    inst = preparar(materias, [estudiante("e01", *[(c, 3, [f"X{i}"]) for i, c in enumerate(codigos)])])
    a = [Registro("e01", c, f"S{c}") for c in codigos[:4]] + [Registro("e01", codigos[4], None)]
    b = [Registro("e01", c, f"SX{i}", posicion_sustituta=0) for i, c in enumerate(codigos)]
    pa, pb = puntuar(inst, a, 0), puntuar(inst, b, 0)
    assert pa.c == pb.c == (0, 0, 4, 0, 0)  # sin errores de redondeo de 0,8 + 0,8 + ...
    assert (pa.posiciones_sustitutas, pb.posiciones_sustitutas) == (0, 5)
    assert mejor(inst, a, b) == ("A", "posiciones_sustitutas")


def dos_estudiantes_un_cupo(semestre_activo: bool, prioridad_e02: int = 5):
    inst = preparar(
        {"M1": 3},
        [estudiante("e01", ("M1", 5), semestre=2), estudiante("e02", ("M1", prioridad_e02), semestre=8)],
        semestre=semestre_activo,
    )
    gana_e01 = [Registro("e01", "M1", "S1"), Registro("e02", "M1", None)]
    gana_e02 = [Registro("e01", "M1", None), Registro("e02", "M1", "S1")]
    return inst, gana_e01, gana_e02


def test_semestre_activado_gana_el_de_octavo():
    """Tabla 5, caso 'Semestre' (activado)."""
    inst, gana_e01, gana_e02 = dos_estudiantes_un_cupo(True)
    assert mejor(inst, gana_e02, gana_e01) == ("A", "J")


def test_semestre_desactivado_decide_el_codigo():
    """Tabla 5, caso 'Semestre' (desactivado): todo empata y gana la lista que va primero (e01)."""
    inst, gana_e01, gana_e02 = dos_estudiantes_un_cupo(False)
    assert mejor(inst, gana_e01, gana_e02) == ("A", "registros")
    assert puntuar(inst, gana_e01, 0).j is None


def test_el_semestre_nunca_desplaza_una_prioridad_5_por_una_4():
    """Tabla 5, caso 'Límite del semestre': gana la prioridad 5 en ambas configuraciones."""
    for activo in (True, False):
        inst, gana_e01, gana_e02 = dos_estudiantes_un_cupo(activo, prioridad_e02=4)
        assert mejor(inst, gana_e01, gana_e02) == ("A", "C")


def test_las_preferencias_deciden_solo_si_empatan_las_materias():
    inst = preparar({"M1": 3, "M2": 3}, [estudiante("e01", ("M1", 5), ("M2", 5))])
    dos = [Registro("e01", "M1", "S1"), Registro("e01", "M2", "S2")]
    una = [Registro("e01", "M1", "S1"), Registro("e01", "M2", None)]
    # Tabla 5, caso 'Preferencias': más satisfacción no compensa perder una de prioridad 5
    assert mejor(inst, dos, una, sat_a=0.1, sat_b=1.0) == ("A", "C")
    otra = [Registro("e01", "M1", "S1b"), Registro("e01", "M2", "S2")]
    assert mejor(inst, dos, otra, sat_a=0.6, sat_b=0.7) == ("B", "satisfaccion")


def test_resultados_identicos():
    inst = preparar({"M1": 3}, [estudiante("e01", ("M1", 5))])
    r = [Registro("e01", "M1", "S1")]
    assert mejor(inst, r, list(reversed(r)), 0.5, 0.5) == ("=", None)


# ------------------------------------------------------------------ desde la salida


def test_el_resumen_trae_q_completo(correr):
    crudos = instancia(
        {"M1": 3, "M2": 3, "M3": 3},
        [seccion("S3", "M3", sesion("L", "07:00"))],
        [estudiante("e01", ("M1", 4, ["M2", "M3"]), semestre=6)],
        config={"desempate_semestre": True},
    )
    salida = correr(crudos, 4)
    objetivo = salida["resumen"]["objetivo"]
    assert objetivo["c"] == salida["resumen"]["puntaje_lexicografico"] == [0, 0.8, 0, 0, 0]
    assert objetivo["j"] == [0, 4.8, 0, 0, 0]  # 0,8 × semestre 6
    assert objetivo["posiciones_sustitutas"] == 2  # M3 es la segunda sustituta
    assert objetivo["satisfaccion"] == salida["estudiantes"][0]["satisfaccion"]["total"]


def test_sin_desempate_por_semestre_j_es_nulo(correr):
    salida = correr(instancia({"M1": 3}, [seccion("S1", "M1", sesion("L", "07:00"))], [estudiante("e01", ("M1", 5))]), 4)
    assert salida["resumen"]["objetivo"]["j"] is None
