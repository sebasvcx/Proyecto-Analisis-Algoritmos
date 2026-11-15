"""Precondiciones de la entrada (Sección 5.6): errores con archivo, registro y campo."""

from asignador.datos import construir_instancia
from tests.constructores import estudiante, instancia, seccion, sesion


def base(**cambios):
    datos = instancia(
        {"M1": 3, "M2": 3},
        [seccion("S1", "M1", sesion("L", "07:00")), seccion("S2", "M2", sesion("M", "07:00"))],
        [estudiante("e01", ("M1", 5)), estudiante("e02", ("M2", 3))],
    )
    datos.update(cambios)
    return datos


def errores(crudos):
    _, reporte = construir_instancia(crudos)
    return [(p.archivo, p.registro, p.campo) for p in reporte.errores]


def test_instancia_valida():
    inst, reporte = construir_instancia(base())
    assert reporte.es_valido
    assert set(inst.estudiantes) == {"e01", "e02"}


def test_profesor_inexistente_detiene_la_ejecucion():
    crudos = base(secciones=[seccion("S1", "M1", sesion("L", "07:00"), profesor="P99")])
    assert ("secciones.json", "S1", "profesor") in errores(crudos)


def test_cupo_no_positivo():
    crudos = base(secciones=[seccion("S1", "M1", sesion("L", "07:00"), cupo=0)])
    assert ("secciones.json", "S1", "cupo") in errores(crudos)


def test_sesion_que_no_dura_dos_horas():
    mala = {"dia": "L", "inicio": "07:00", "fin": "10:00", "edificio": "B1", "salon": "B1-101"}
    assert ("secciones.json", "S1", "sesiones[0]") in errores(base(secciones=[seccion("S1", "M1", mala)]))


def test_sesion_despues_de_las_20():
    assert errores(base(secciones=[seccion("S1", "M1", sesion("L", "19:00"))]))


def test_profesor_con_dos_secciones_simultaneas():
    crudos = base(secciones=[seccion("S1", "M1", sesion("L", "07:00", salon="X")), seccion("S2", "M2", sesion("L", "08:00", salon="Y"))])
    assert any(campo == "profesor" for _, _, campo in errores(crudos))


def test_identificador_repetido():
    crudos = base(secciones=[seccion("S1", "M1", sesion("L", "07:00")), seccion("S1", "M2", sesion("M", "07:00"))])
    assert ("secciones.json", "S1", "id") in errores(crudos)


def test_sustituta_que_tambien_es_principal():
    crudos = base(estudiantes=[estudiante("e01", ("M1", 5, ["M2"]), ("M2", 3))])
    assert ("estudiantes.json", "e01", "materias[0].sustitutas") in errores(crudos)


def test_preferencia_social_hacia_si_mismo():
    crudos = base(estudiantes=[estudiante("e01", ("M1", 5), social=[{"estudiante": "e01", "afinidad": 2}])])
    assert ("estudiantes.json", "e01", "social") in errores(crudos)


def test_traslado_faltante():
    crudos = instancia({"M1": 3}, [], [], edificios=("A", "B"), traslados=[])
    assert ("traslados.json", "A→B", "") in errores(crudos)


def test_dia_comodin_se_expande_a_seis_dias():
    libres = [{"dia": "*", "inicio": "13:00", "fin": "14:00", "tipo": "obligatoria"}]
    inst, _ = construir_instancia(base(estudiantes=[estudiante("e01", ("M1", 5), franjas_libres=libres)]))
    assert len(inst.estudiantes["e01"].preferencias.franjas_obligatorias) == 6


def test_demanda_mayor_que_cupos_es_solo_advertencia():
    crudos = base(secciones=[seccion("S1", "M1", sesion("L", "07:00"), cupo=1), seccion("S2", "M2", sesion("M", "07:00"))])
    crudos["estudiantes"] = [estudiante("e01", ("M1", 5)), estudiante("e02", ("M1", 5))]
    inst, reporte = construir_instancia(crudos)
    assert inst is not None
    assert any("supera" in p.mensaje for p in reporte.advertencias)


def test_conjunto_vacio_es_valido():
    inst, reporte = construir_instancia(instancia({}, [], []))
    assert reporte.es_valido and inst.estudiantes == {}
