import pytest
from fastapi.testclient import TestClient

from api.ajustes import Ajustes, obtener_ajustes
from api.main import crear_app


@pytest.fixture
def cliente(tmp_path):
    app = crear_app()
    ajustes = Ajustes(tmp_path / "data", tmp_path / "resultados", tmp_path / "respaldos", ("*",))
    app.dependency_overrides[obtener_ajustes] = lambda: ajustes
    return TestClient(app)


def test_sin_datos_reporta_archivos_faltantes(cliente):
    r = cliente.get("/api/datos").json()
    assert r["validacion"]["errores"] == 6  # todos menos config.json, que es opcional


def test_flujo_generar_ejecutar_consultar(cliente):
    r = cliente.post("/api/datos/generar", json={"estudiantes": 30, "secciones": 50, "semilla": 1})
    assert r.status_code == 200
    assert r.json()["validacion"]["errores"] == 0

    corrida = cliente.post("/api/corridas", json={"nivel": 10})
    assert corrida.status_code == 201
    cuerpo = corrida.json()
    assert cuerpo["verificacion"]["total"] == 0
    assert len(cuerpo["estudiantes"]) == 30

    lista = cliente.get("/api/corridas").json()
    assert [c["id"] for c in lista] == [cuerpo["corrida"]["id"]]
    assert cliente.get(f"/api/corridas/{cuerpo['corrida']['id']}").json()["corrida"]["nivel"] == 10
    secciones = cliente.get(f"/api/corridas/{cuerpo['corrida']['id']}/entrada/secciones").json()
    assert len(secciones) == 50


def test_nivel_inexistente(cliente):
    cliente.post("/api/datos/generar", json={"estudiantes": 5, "secciones": 42})
    r = cliente.post("/api/corridas", json={"nivel": 11})
    assert r.status_code == 422


def test_datos_invalidos_impiden_ejecutar(cliente):
    cliente.post("/api/datos/generar", json={"estudiantes": 5, "secciones": 42})
    secciones = cliente.get("/api/datos/secciones").json()
    secciones[0]["profesor"] = "no-existe"
    assert cliente.put("/api/datos/secciones", json=secciones).json()["validacion"]["errores"] == 1
    assert cliente.post("/api/corridas", json={"nivel": 1}).status_code == 422


def test_reemplazar_con_tipo_incorrecto(cliente):
    assert cliente.put("/api/datos/materias", json={"no": "lista"}).status_code == 422


def test_ruta_de_corrida_no_permite_salir_de_resultados(cliente):
    assert cliente.get("/api/corridas/..%2F..%2Fetc").status_code == 404
