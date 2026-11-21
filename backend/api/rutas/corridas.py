from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, HTTPException

from asignador.algoritmo import NIVELES, NivelNoDisponible
from asignador.corrida import ejecutar_corrida, guardar_corrida, leer_corrida, leer_entrada_corrida, listar_corridas
from asignador.experimentos import ejecutar_metodo, fila_resumen
from asignador.referencias import ejecutar_referencia

from ..dependencias import AjustesDep, Repositorio
from ..esquemas import PeticionCorrida

router = APIRouter(prefix="/api", tags=["corridas"])


@router.get("/niveles")
def niveles() -> list[dict]:
    return [
        {"numero": n.numero, "nombre": n.nombre, "descripcion": n.descripcion, "disponible": n.disponible, "reglas": list(n.reglas_cubiertas)}
        for n in NIVELES.values()
    ]


@router.get("/corridas")
def corridas(ajustes: AjustesDep) -> list[dict]:
    return listar_corridas(ajustes.carpeta_resultados)


@router.get("/corridas/{identificador}")
def corrida(identificador: str, ajustes: AjustesDep) -> dict:
    salida = leer_corrida(ajustes.carpeta_resultados, identificador)
    if salida is None:
        raise HTTPException(404, f"no existe la corrida '{identificador}'")
    return salida


@router.get("/corridas/{identificador}/entrada/{entidad}")
def entrada(identificador: str, entidad: str, ajustes: AjustesDep):
    contenido = leer_entrada_corrida(ajustes.carpeta_resultados, identificador, entidad)
    if contenido is None:
        raise HTTPException(404, f"la corrida '{identificador}' no tiene '{entidad}'")
    return contenido


@router.post("/corridas", status_code=201)
def ejecutar(peticion: PeticionCorrida, repo: Repositorio, ajustes: AjustesDep) -> dict:
    instancia, reporte, crudos = repo.cargar()
    if instancia is None:
        raise HTTPException(
            422,
            {"mensaje": "los datos tienen errores; corríjalos antes de ejecutar", "problemas": [p.como_dict() for p in reporte.errores]},
        )
    if peticion.desempate_semestre is not None:
        instancia.configuracion = replace(instancia.configuracion, desempate_semestre=peticion.desempate_semestre)
    try:
        if peticion.referencia is not None:
            salida = ejecutar_referencia(instancia, peticion.referencia, peticion.semilla_referencia)
        else:
            salida = ejecutar_corrida(instancia, peticion.nivel)
    except NivelNoDisponible as exc:
        raise HTTPException(422, str(exc)) from exc
    guardar_corrida(ajustes.carpeta_resultados, salida, crudos)
    return salida


@router.post("/comparacion")
def comparacion(repo: Repositorio) -> list[dict]:
    """Ejecuta las referencias y todos los niveles disponibles sobre los datos actuales, sin guardar.

    Alimenta la gráfica de comparación entre niveles de la pantalla Resultados.
    """
    instancia, reporte, _ = repo.cargar()
    if instancia is None:
        raise HTTPException(422, {"mensaje": "los datos tienen errores; corríjalos antes de comparar", "problemas": [p.como_dict() for p in reporte.errores]})
    metodos = [("aleatoria", "Aleatoria"), ("llegada", "Llegada")] + [(f"N{n.numero}", f"N{n.numero}") for n in NIVELES.values() if n.disponible]
    semilla = instancia.configuracion.semilla
    return [
        {"metodo": metodo, "etiqueta": etiqueta, **fila_resumen(ejecutar_metodo(instancia, metodo, semilla))}
        for metodo, etiqueta in metodos
    ]
