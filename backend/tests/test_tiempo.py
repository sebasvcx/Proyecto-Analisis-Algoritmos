import pytest

from asignador.dominio import Franja, a_hora, a_minutos


def f(dia, inicio, fin):
    return Franja(dia, a_minutos(inicio), a_minutos(fin))


def test_sesiones_seguidas_no_se_cruzan():
    assert not f("L", "07:00", "09:00").se_cruza_con(f("L", "09:00", "11:00"))


def test_solape_parcial_se_cruza():
    assert f("L", "07:00", "09:00").se_cruza_con(f("L", "08:00", "10:00"))


def test_dias_distintos_no_se_cruzan():
    assert not f("L", "07:00", "09:00").se_cruza_con(f("M", "07:00", "09:00"))


def test_contiene():
    assert f("L", "14:00", "20:00").contiene(f("L", "16:00", "18:00"))
    assert not f("L", "14:00", "20:00").contiene(f("L", "13:00", "15:00"))


@pytest.mark.parametrize("texto", ["7:00", "24:00", "07:60", "abc"])
def test_hora_invalida(texto):
    with pytest.raises(ValueError):
        a_minutos(texto)


def test_ida_y_vuelta():
    assert a_hora(a_minutos("18:00")) == "18:00"
