"""Servidor FastAPI: lee y escribe los JSON de `data/` y lanza las corridas.

Desarrollo:  uvicorn api.main:app --reload   (desde backend/)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from asignador import __version__

from .ajustes import obtener_ajustes
from .rutas import corridas, datos, estudiantes


def crear_app() -> FastAPI:
    app = FastAPI(title="Asignador de horarios", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(obtener_ajustes().origenes_cors),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(datos.router)
    app.include_router(corridas.router)
    app.include_router(estudiantes.router)

    @app.get("/api/salud", tags=["sistema"])
    def salud() -> dict:
        return {"estado": "ok", "version": __version__}

    return app


app = crear_app()
