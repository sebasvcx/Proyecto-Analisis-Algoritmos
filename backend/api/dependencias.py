from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from .ajustes import Ajustes, obtener_ajustes
from .repositorio import RepositorioDatos


def obtener_repositorio(ajustes: Annotated[Ajustes, Depends(obtener_ajustes)]) -> RepositorioDatos:
    return RepositorioDatos(ajustes.carpeta_datos, ajustes.carpeta_respaldos)


Repositorio = Annotated[RepositorioDatos, Depends(obtener_repositorio)]
AjustesDep = Annotated[Ajustes, Depends(obtener_ajustes)]
