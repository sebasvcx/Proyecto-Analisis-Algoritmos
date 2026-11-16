"""Satisfacción de preferencias (Sección 5.5): cada criterio por separado y el agregado."""

import pytest

from asignador import satisfaccion as sat
from asignador.datos import cargar_instancia
from tests.constructores import estudiante, instancia, seccion, sesion

MANANA = [{"dia": "*", "inicio": "07:00", "fin": "13:00"}]


def preparar(secciones: list[dict], *estudiantes: dict, **kwargs):
    crudos = instancia({"M1": 3, "M2": 3, "M3": 3}, secciones, list(estudiantes), **kwargs)
    inst = cargar_instancia(crudos)
    return inst, inst.estudiantes


def secs(inst, *ids):
    return [inst.secciones[i] for i in ids]


# ------------------------------------------------------------------ profesores


def test_profesores_promedia_afinidades():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1"), seccion("S2", "M2", sesion("M", "07:00"), profesor="P2")],
        estudiante("e01", profesores=[{"id": "P1", "afinidad": 2}, {"id": "P2", "afinidad": -1}]),
    )
    # (2+2)/4 = 1 y (-1+2)/4 = 0,25 → 0,625
    assert sat.profesores(est["e01"], secs(inst, "S1", "S2")) == pytest.approx(0.625)


def test_profesor_sin_afinidad_declarada_vale_cero():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1"), seccion("S2", "M2", sesion("M", "07:00"), profesor="P2")],
        estudiante("e01", profesores=[{"id": "P1", "afinidad": 2}]),
    )
    assert sat.profesores(est["e01"], secs(inst, "S1", "S2")) == pytest.approx((1 + 0.5) / 2)


def test_profesores_se_omite_sin_afinidades_o_sin_secciones():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00"))],
        estudiante("e01"),
        estudiante("e02", profesores=[{"id": "P1", "afinidad": 2}]),
    )
    assert sat.profesores(est["e01"], secs(inst, "S1")) is None
    assert sat.profesores(est["e02"], []) is None


# ------------------------------------------------------------------ horario


def test_horario_franjas_preferidas():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00")), seccion("S2", "M2", sesion("L", "14:00"))],
        estudiante("e01", franjas_preferidas=MANANA),
    )
    assert sat.horario(est["e01"], secs(inst, "S1", "S2")) == pytest.approx(0.5)


def test_horario_promedia_los_tipos_declarados():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00")), seccion("S2", "M2", sesion("L", "14:00"))],
        estudiante("e01", franjas_preferidas=MANANA, franjas_evitadas=[{"dia": "*", "inicio": "07:00", "fin": "08:00"}]),
    )
    # preferidas: 120/240 = 0,5; evitadas: 1 − 60/240 = 0,75 → 0,625
    assert sat.horario(est["e01"], secs(inst, "S1", "S2")) == pytest.approx(0.625)


def test_horario_libres_deseables_cuentan_minutos_fuera():
    almuerzo = [{"dia": "*", "inicio": "12:00", "fin": "14:00", "tipo": "deseable"}]
    inst, est = preparar([seccion("S1", "M1", sesion("L", "11:00"))], estudiante("e01", franjas_libres=almuerzo))
    assert sat.horario(est["e01"], secs(inst, "S1")) == pytest.approx(0.5)


def test_horario_no_cuenta_minutos_repetidos():
    solapadas = [{"dia": "L", "inicio": "07:00", "fin": "11:00"}, {"dia": "L", "inicio": "09:00", "fin": "13:00"}]
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00")), seccion("S2", "M2", sesion("L", "09:00"))],
        estudiante("e01", franjas_preferidas=solapadas),
    )
    assert sat.horario(est["e01"], secs(inst, "S1", "S2")) == pytest.approx(1.0)


def test_horario_franja_obligatoria_no_cuenta():
    trabajo = [{"dia": "L", "inicio": "14:00", "fin": "20:00", "tipo": "obligatoria"}]
    inst, est = preparar([seccion("S1", "M1", sesion("M", "16:00"))], estudiante("e01", franjas_libres=trabajo))
    assert sat.horario(est["e01"], secs(inst, "S1")) is None


def test_horario_se_omite_sin_clases():
    inst, est = preparar([], estudiante("e01", franjas_preferidas=MANANA))
    assert sat.horario(est["e01"], []) is None


# ------------------------------------------------------------------ cercanía

TRES_EDIFICIOS = dict(
    edificios=("A", "B", "C"),
    traslados=[
        {"origen": "A", "destino": "B", "minutos": 10},
        {"origen": "A", "destino": "C", "minutos": 20},
        {"origen": "B", "destino": "C", "minutos": 15},
    ],
)


def test_cercania_relativa_al_mayor_traslado():
    inst, _ = preparar(
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "09:00", "B"))],
        estudiante("e01"),
        **TRES_EDIFICIOS,
    )
    # caminata promedio 10, mayor traslado del campus 20 → 1 − 10/20
    assert sat.cercania(inst, secs(inst, "S1", "S2")) == pytest.approx(0.5)


def test_cercania_vale_uno_si_todos_los_traslados_son_cero():
    inst, _ = preparar(
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("L", "09:00", "B"))],
        estudiante("e01"),
        edificios=("A", "B"),
        traslados=[{"origen": "A", "destino": "B", "minutos": 0}],
    )
    assert sat.cercania(inst, secs(inst, "S1", "S2")) == 1.0


def test_cercania_se_omite_sin_clases_consecutivas():
    inst, _ = preparar(
        [seccion("S1", "M1", sesion("L", "07:00", "A")), seccion("S2", "M2", sesion("M", "09:00", "C"))],
        estudiante("e01"),
        **TRES_EDIFICIOS,
    )
    assert sat.cercania(inst, secs(inst, "S1", "S2")) is None


# ------------------------------------------------------------------ huecos


def test_huecos_cuenta_minutos_libres_entre_clases_del_mismo_dia():
    inst, _ = preparar(
        [seccion("S1", "M1", sesion("L", "07:00")), seccion("S2", "M2", sesion("L", "11:00")), seccion("S3", "M3", sesion("M", "16:00"))],
        estudiante("e01"),
    )
    # 09:00–11:00 libre el lunes; el martes no hay hueco
    assert sat.huecos(secs(inst, "S1", "S2", "S3")) == pytest.approx(1 - 120 / 4680)


def test_huecos_clases_seguidas_no_tienen_hueco_y_sin_clases_se_omite():
    inst, _ = preparar([seccion("S1", "M1", sesion("L", "07:00")), seccion("S2", "M2", sesion("L", "09:00"))], estudiante("e01"))
    assert sat.huecos(secs(inst, "S1", "S2")) == 1.0
    assert sat.huecos([]) is None


# ------------------------------------------------------------------ compañeros


def test_social_amigo_que_comparte_y_persona_a_evitar_que_comparte():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00"))],
        estudiante("e01", social=[{"estudiante": "e02", "afinidad": 2}, {"estudiante": "e03", "afinidad": -2}]),
        estudiante("e02"),
        estudiante("e03"),
    )
    secciones_de = {"e01": ["S1"], "e02": ["S1"], "e03": ["S1"]}
    # amigo comparte → 1 (peso 2); a evitar comparte → 0 (peso 2)
    assert sat.social(est["e01"], secs(inst, "S1"), secciones_de) == pytest.approx(0.5)


def test_social_pondera_por_el_valor_absoluto():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00"))],
        estudiante("e01", social=[{"estudiante": "e02", "afinidad": 1}, {"estudiante": "e03", "afinidad": -2}]),
        estudiante("e02"),
        estudiante("e03"),
    )
    secciones_de = {"e01": ["S1"], "e02": [], "e03": []}
    # amigo no comparte → 0 (peso 1); a evitar no comparte → 1 (peso 2)
    assert sat.social(est["e01"], secs(inst, "S1"), secciones_de) == pytest.approx(2 / 3)


def test_social_omite_afinidad_cero():
    inst, est = preparar(
        [],
        estudiante("e01", social=[{"estudiante": "e02", "afinidad": 0}]),
        estudiante("e02"),
    )
    assert sat.social(est["e01"], [], {}) is None


# ------------------------------------------------------------------ agregado


def test_total_pondera_por_importancia_declarada():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "16:00"), profesor="P1")],
        estudiante(
            "e01",
            profesores=[{"id": "P1", "afinidad": 2}],
            franjas_preferidas=MANANA,
            importancia={"profesores": "alta", "horario": "baja", "huecos": "ninguna"},
        ),
    )
    s = sat.calcular(inst, est["e01"], secs(inst, "S1"), {})
    # profesores 1,0 × 3 + horario 0,0 × 1; huecos tiene peso 0 y cercanía/social no son evaluables
    assert s.total == pytest.approx(0.75)
    assert s.criterios["huecos"].peso == 0
    assert s.criterios["cercania"].valor is None


def test_pesos_por_defecto_dos_y_huecos_uno():
    inst, est = preparar([seccion("S1", "M1", sesion("L", "07:00"))], estudiante("e01"))
    pesos = {c: k.peso for c, k in sat.calcular(inst, est["e01"], [], {}).criterios.items()}
    assert pesos == {"profesores": 2, "horario": 2, "cercania": 2, "huecos": 1, "social": 2}


def test_sin_criterios_evaluables_vale_neutro():
    inst, est = preparar([], estudiante("e01"))
    s = sat.calcular(inst, est["e01"], [], {})
    assert s.total == 0.5
    assert not s.evaluable
    assert s.como_dict()["criterios"]["horario"] == {"valor": 0.5, "evaluable": False, "peso": 2}


def test_criterios_activos_y_pesos_por_defecto_para_los_niveles():
    inst, est = preparar(
        [seccion("S1", "M1", sesion("L", "07:00"))],
        estudiante("e01", importancia={"profesores": "alta"}),
    )
    s = sat.calcular(inst, est["e01"], secs(inst, "S1"), {}, criterios=("profesores",), pesos_declarados=False)
    assert list(s.criterios) == ["profesores"]
    assert s.criterios["profesores"].peso == 2


# ------------------------------------------------------------------ en la salida


def test_la_salida_incluye_satisfaccion_por_estudiante_y_resumen(correr):
    crudos = instancia(
        {"M1": 3},
        [seccion("S1", "M1", sesion("L", "07:00"), profesor="P1")],
        [
            estudiante("e01", ("M1", 5), profesores=[{"id": "P1", "afinidad": 2}], importancia={"huecos": "ninguna"}),
            estudiante("e02", ("M1", 5), profesores=[{"id": "P1", "afinidad": -2}], importancia={"huecos": "ninguna"}),
            estudiante("e03"),
        ],
    )
    salida = correr(crudos, 4)
    por_id = {e["id"]: e["satisfaccion"] for e in salida["estudiantes"]}
    assert por_id["e01"]["total"] == 1.0
    assert por_id["e02"]["total"] == 0.0
    assert por_id["e03"] == {**por_id["e03"], "total": 0.5, "evaluable": False}
    resumen = salida["resumen"]["satisfaccion"]
    # e03 no tiene nada evaluable y no entra al promedio ni al mínimo
    assert resumen["estudiantes_evaluables"] == 2
    assert resumen["promedio"] == 0.5
    assert resumen["minimo"] == 0.0
    assert resumen["por_criterio"]["profesores"] == 0.5
    assert resumen["por_criterio"]["cercania"] is None


def test_sin_estudiantes_evaluables_el_resumen_no_aplica(correr):
    salida = correr(instancia({}, [], [estudiante("e01")]), 4)
    assert salida["resumen"]["satisfaccion"]["promedio"] is None
    assert salida["resumen"]["satisfaccion"]["minimo"] is None
