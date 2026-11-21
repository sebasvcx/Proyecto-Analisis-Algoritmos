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


def test_corrida_de_referencia_y_casilla_de_semestre(cliente):
    cliente.post("/api/datos/generar", json={"estudiantes": 20, "secciones": 45, "semilla": 4})
    ref = cliente.post("/api/corridas", json={"referencia": "llegada"}).json()
    assert ref["corrida"]["referencia"] == "llegada"
    assert ref["verificacion"]["total"] == 0

    n10 = cliente.post("/api/corridas", json={"nivel": 10, "desempate_semestre": True}).json()
    assert n10["corrida"]["configuracion"]["desempate_semestre"] is True
    assert n10["resumen"]["objetivo"]["j"] is not None
    # la casilla no modifica config.json
    assert cliente.get("/api/datos").json()["configuracion"].get("desempate_semestre") is False

    lista = cliente.get("/api/corridas").json()
    assert {c["referencia"] for c in lista} == {"llegada", None}


def test_guardar_preferencias_valida_antes_de_escribir(cliente):
    cliente.post("/api/datos/generar", json={"estudiantes": 10, "secciones": 42, "semilla": 2})
    estudiantes = cliente.get("/api/datos/estudiantes").json()
    est = estudiantes[0]
    materia = cliente.get("/api/datos/materias").json()[0]["codigo"]

    malo = {**est, "materias": [{"codigo": "NO-EXISTE", "prioridad": 9}]}
    r = cliente.put(f"/api/estudiantes/{est['id']}", json=malo)
    assert r.status_code == 422
    campos = {p["campo"] for p in r.json()["detail"]["problemas"]}
    assert "materias[0].prioridad" in campos
    # no se escribió nada
    assert cliente.get("/api/datos/estudiantes").json()[0] == est

    bueno = {**est, "materias": [{"codigo": materia, "prioridad": 5}], "importancia": {"horario": "alta"}}
    r = cliente.put(f"/api/estudiantes/{est['id']}", json=bueno)
    assert r.status_code == 200 and r.json()["creado"] is False
    assert cliente.get("/api/datos/estudiantes").json()[0]["importancia"] == {"horario": "alta"}


def test_guardar_estudiante_nuevo_y_codigo_distinto(cliente):
    cliente.post("/api/datos/generar", json={"estudiantes": 3, "secciones": 42})
    nuevo = {"id": "e900", "nombre": "Nueva Persona", "semestre": 1, "materias": []}
    assert cliente.put("/api/estudiantes/e900", json=nuevo).json()["creado"] is True
    assert len(cliente.get("/api/datos/estudiantes").json()) == 4
    assert cliente.put("/api/estudiantes/e901", json=nuevo).status_code == 422


def test_comparacion_entre_niveles(cliente):
    cliente.post("/api/datos/generar", json={"estudiantes": 25, "secciones": 45, "semilla": 6})
    filas = cliente.post("/api/comparacion").json()
    assert [f["etiqueta"] for f in filas] == ["Aleatoria", "Llegada"] + [f"N{n}" for n in range(1, 11)]
    assert all(f["violaciones"] == 0 for f in filas if f["metodo"] not in ("N1", "N2"))
