"""Convierte el contenido de los JSON en los TADs del dominio.

Cada error indica archivo, registro y campo, como pide la precondición de la
Sección 5.6. La lectura no se detiene en el primer error: se recolectan todos
para mostrarlos juntos en la pantalla de Datos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..dominio import (
    Configuracion,
    Edificio,
    Estudiante,
    Franja,
    Importancia,
    Instancia,
    Materia,
    Preferencias,
    Profesor,
    Seccion,
    Sesion,
    Solicitud,
    a_minutos,
)
from ..dominio.tiempo import DIAS, DURACION_SESION, HORA_APERTURA, HORA_CIERRE, TODOS_LOS_DIAS, expandir_dias
from .problemas import DatosInvalidos, Reporte
from .validacion import validar_coherencia

CRITERIOS = ("horario", "profesores", "cercania", "huecos", "social")
_IMPORTANCIAS = {"ninguna": Importancia.NINGUNA, "baja": Importancia.BAJA, "media": Importancia.MEDIA, "alta": Importancia.ALTA}


@dataclass
class _Lugar:
    """Dónde estamos leyendo, para construir mensajes precisos."""

    reporte: Reporte
    archivo: str
    registro: str = ""

    def error(self, campo: str, mensaje: str) -> None:
        self.reporte.error(self.archivo, self.registro, campo, mensaje)

    def texto(self, datos: dict, campo: str, prefijo: str = "") -> str | None:
        """`prefijo` ubica el campo dentro de una lista, p. ej. 'materias[0].'."""
        valor = datos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            self.error(prefijo + campo, "se espera un texto no vacío")
            return None
        return valor.strip()

    def entero(self, datos: dict, campo: str, minimo: int, maximo: int | None = None, prefijo: str = "") -> int | None:
        valor = datos.get(campo)
        if isinstance(valor, bool) or not isinstance(valor, int):
            self.error(prefijo + campo, "se espera un número entero")
            return None
        if valor < minimo or (maximo is not None and valor > maximo):
            rango = f"entre {minimo} y {maximo}" if maximo is not None else f"mayor o igual a {minimo}"
            self.error(prefijo + campo, f"el valor {valor} debe estar {rango}")
            return None
        return valor


def _lista(crudos: dict[str, Any], entidad: str, reporte: Reporte) -> list[dict]:
    contenido = crudos.get(entidad, [])
    archivo = f"{entidad}.json"
    if not isinstance(contenido, list):
        reporte.error(archivo, "", "", "el archivo debe contener una lista de registros")
        return []
    registros = []
    for i, registro in enumerate(contenido):
        if isinstance(registro, dict):
            registros.append(registro)
        else:
            reporte.error(archivo, f"posición {i}", "", "cada registro debe ser un objeto")
    return registros


def _indexar(registros, clave, lugar: _Lugar, construir):
    """Construye un dict id -> entidad y detecta identificadores repetidos."""
    resultado = {}
    for i, datos in enumerate(registros):
        lugar.registro = str(datos.get(clave) or f"posición {i}")
        entidad = construir(datos, lugar)
        if entidad is None:
            continue
        identificador = getattr(entidad, clave)
        if identificador in resultado:
            lugar.error(clave, f"identificador repetido '{identificador}'")
            continue
        resultado[identificador] = entidad
    return resultado


# ---------------------------------------------------------------- oferta


def _materia(d: dict, lugar: _Lugar) -> Materia | None:
    codigo, nombre = lugar.texto(d, "codigo"), lugar.texto(d, "nombre")
    creditos = lugar.entero(d, "creditos", 1, 6)
    semestre = lugar.entero(d, "semestre", 1, 10)
    if None in (codigo, nombre, creditos, semestre):
        return None
    return Materia(codigo, nombre, creditos, semestre)


def _profesor(d: dict, lugar: _Lugar) -> Profesor | None:
    pid, nombre = lugar.texto(d, "id"), lugar.texto(d, "nombre")
    if None in (pid, nombre):
        return None
    return Profesor(pid, nombre, str(d.get("departamento", "")))


def _edificio(d: dict, lugar: _Lugar) -> Edificio | None:
    eid, nombre = lugar.texto(d, "id"), lugar.texto(d, "nombre")
    if None in (eid, nombre):
        return None
    return Edificio(eid, nombre)


def _franjas(d: dict, lugar: _Lugar, campo: str, *, sesion: bool = False) -> list[Franja] | None:
    """Lee una franja (o varias, si el día es '*'). Devuelve None si es inválida."""
    dia = d.get("dia")
    validos = DIAS if sesion else (*DIAS, TODOS_LOS_DIAS)
    if dia not in validos:
        lugar.error(f"{campo}.dia", f"día '{dia}' inválido; se espera uno de {', '.join(validos)}")
        return None
    try:
        inicio, fin = a_minutos(str(d.get("inicio"))), a_minutos(str(d.get("fin")))
    except ValueError as exc:
        lugar.error(campo, str(exc))
        return None
    if inicio % 60 or fin % 60:
        lugar.error(campo, "las horas deben ser en punto")
        return None
    if not (HORA_APERTURA <= inicio < fin <= HORA_CIERRE):
        lugar.error(campo, "el inicio debe ser anterior al fin y ambos entre 07:00 y 20:00")
        return None
    if sesion and fin - inicio != DURACION_SESION:
        lugar.error(campo, "cada sesión debe durar exactamente 2 horas")
        return None
    return [Franja(dia_real, inicio, fin) for dia_real in expandir_dias(dia)]


def _seccion(d: dict, lugar: _Lugar) -> Seccion | None:
    sid, materia, profesor = lugar.texto(d, "id"), lugar.texto(d, "materia"), lugar.texto(d, "profesor")
    cupo = lugar.entero(d, "cupo", 1)
    crudas = d.get("sesiones")
    if not isinstance(crudas, list) or not crudas:
        lugar.error("sesiones", "se espera al menos una sesión")
        return None
    sesiones = []
    for i, s in enumerate(crudas):
        campo = f"sesiones[{i}]"
        if not isinstance(s, dict):
            lugar.error(campo, "cada sesión debe ser un objeto")
            continue
        franjas = _franjas(s, lugar, campo, sesion=True)
        edificio, salon = lugar.texto(s, "edificio"), lugar.texto(s, "salon")
        if franjas and edificio and salon:
            sesiones.append(Sesion(franjas[0], edificio, salon))
    if None in (sid, materia, profesor, cupo) or len(sesiones) != len(crudas):
        return None
    return Seccion(sid, materia, profesor, cupo, tuple(sorted(sesiones, key=lambda s: s.franja)))


def _traslados(registros: list[dict], reporte: Reporte) -> dict[tuple[str, str], int]:
    lugar = _Lugar(reporte, "traslados.json")
    traslados: dict[tuple[str, str], int] = {}
    for i, d in enumerate(registros):
        lugar.registro = f"posición {i}"
        origen, destino = lugar.texto(d, "origen"), lugar.texto(d, "destino")
        minutos = lugar.entero(d, "minutos", 0)
        if None in (origen, destino, minutos):
            continue
        for par in ((origen, destino), (destino, origen)):
            previo = traslados.get(par)
            if previo is not None and previo != minutos:
                lugar.error("minutos", f"{origen}↔{destino} tiene tiempos distintos ({previo} y {minutos})")
            traslados[par] = minutos
    return traslados


# ---------------------------------------------------------------- estudiantes


def _preferencias(d: dict, lugar: _Lugar) -> Preferencias:
    obligatorias, deseables, preferidas, evitadas = [], [], [], []
    for i, f in enumerate(d.get("franjas_libres") or []):
        campo = f"franjas_libres[{i}]"
        tipo = f.get("tipo", "obligatoria") if isinstance(f, dict) else None
        if tipo not in ("obligatoria", "deseable"):
            lugar.error(f"{campo}.tipo", "se espera 'obligatoria' o 'deseable'")
            continue
        franjas = _franjas(f, lugar, campo)
        if franjas:
            (obligatorias if tipo == "obligatoria" else deseables).extend(franjas)
    for campo, destino in (("franjas_preferidas", preferidas), ("franjas_evitadas", evitadas)):
        for i, f in enumerate(d.get(campo) or []):
            franjas = _franjas(f, lugar, f"{campo}[{i}]") if isinstance(f, dict) else None
            if franjas:
                destino.extend(franjas)

    afinidad: dict[str, int] = {}
    vetados: set[str] = set()
    for i, p in enumerate(d.get("profesores") or []):
        campo = f"profesores[{i}]"
        pid = lugar.texto(p, "id", f"profesores[{i}].") if isinstance(p, dict) else None
        if pid is None:
            continue
        if p.get("veto") is True:
            vetados.add(pid)
        if "afinidad" in p:
            valor = lugar.entero(p, "afinidad", -2, 2, f"profesores[{i}].")
            if valor is not None:
                afinidad[pid] = valor
        elif p.get("veto") is not True:
            lugar.error(campo, "indique 'afinidad' (-2 a 2) o 'veto': true")

    social: dict[str, int] = {}
    for i, s in enumerate(d.get("social") or []):
        otro = lugar.texto(s, "estudiante", f"social[{i}].") if isinstance(s, dict) else None
        valor = lugar.entero(s, "afinidad", -2, 2, f"social[{i}].") if isinstance(s, dict) else None
        if otro is not None and valor is not None:
            social[otro] = valor

    importancia: dict[str, Importancia] = {}
    for criterio, valor in (d.get("importancia") or {}).items():
        if criterio not in CRITERIOS:
            lugar.error(f"importancia.{criterio}", f"criterio desconocido; use {', '.join(CRITERIOS)}")
        elif valor not in _IMPORTANCIAS:
            lugar.error(f"importancia.{criterio}", "se espera alta, media, baja o ninguna")
        else:
            importancia[criterio] = _IMPORTANCIAS[valor]

    return Preferencias(
        franjas_obligatorias=tuple(obligatorias),
        franjas_deseables=tuple(deseables),
        franjas_preferidas=tuple(preferidas),
        franjas_evitadas=tuple(evitadas),
        afinidad_profesores=afinidad,
        vetados=frozenset(vetados),
        social=social,
        importancia=importancia,
    )


def _estudiante(d: dict, lugar: _Lugar) -> Estudiante | None:
    eid, nombre = lugar.texto(d, "id"), lugar.texto(d, "nombre")
    semestre = lugar.entero(d, "semestre", 1, 10)
    solicitudes = []
    for i, s in enumerate(d.get("materias") or []):
        campo = f"materias[{i}]"
        if not isinstance(s, dict):
            lugar.error(campo, "cada solicitud debe ser un objeto")
            continue
        codigo = lugar.texto(s, "codigo", f"{campo}.")
        prioridad = lugar.entero(s, "prioridad", 1, 5, f"{campo}.")
        sustitutas = s.get("sustitutas") or []
        if not isinstance(sustitutas, list) or not all(isinstance(x, str) for x in sustitutas):
            lugar.error(f"{campo}.sustitutas", "se espera una lista de códigos")
            continue
        if codigo and prioridad:
            solicitudes.append(Solicitud(codigo, prioridad, tuple(sustitutas)))
    preferencias = _preferencias(d, lugar)
    if None in (eid, nombre, semestre):
        return None
    return Estudiante(eid, nombre, semestre, tuple(solicitudes), preferencias)


def _configuracion(crudo: Any, reporte: Reporte) -> Configuracion:
    if crudo is None:
        return Configuracion()
    if not isinstance(crudo, dict):
        reporte.error("config.json", "", "", "el archivo debe ser un objeto")
        return Configuracion()
    lugar = _Lugar(reporte, "config.json")
    base = Configuracion()
    valores = {}
    if "max_creditos" in crudo:
        valores["max_creditos"] = lugar.entero(crudo, "max_creditos", 1)
    if "semilla" in crudo:
        valores["semilla"] = lugar.entero(crudo, "semilla", 0)
    if "max_cambios" in crudo:
        valores["max_cambios"] = lugar.entero(crudo, "max_cambios", 0)
    if "valor_sustituta" in crudo:
        v = crudo["valor_sustituta"]
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1:
            valores["valor_sustituta"] = float(v)
        else:
            lugar.error("valor_sustituta", "se espera un número entre 0 y 1")
    if "desempate_semestre" in crudo:
        if isinstance(crudo["desempate_semestre"], bool):
            valores["desempate_semestre"] = crudo["desempate_semestre"]
        else:
            lugar.error("desempate_semestre", "se espera true o false")
    return Configuracion(**{**base.__dict__, **{k: v for k, v in valores.items() if v is not None}})


# ---------------------------------------------------------------- entrada


def construir_instancia(crudos: dict[str, Any], fallos_lectura: dict[str, str] | None = None) -> tuple[Instancia | None, Reporte]:
    """Construye y valida una instancia. Devuelve (None, reporte) si hay errores."""
    reporte = Reporte()
    for entidad, mensaje in (fallos_lectura or {}).items():
        reporte.error(f"{entidad}.json", "", "", mensaje)

    materias = _indexar(_lista(crudos, "materias", reporte), "codigo", _Lugar(reporte, "materias.json"), _materia)
    profesores = _indexar(_lista(crudos, "profesores", reporte), "id", _Lugar(reporte, "profesores.json"), _profesor)
    edificios = _indexar(_lista(crudos, "edificios", reporte), "id", _Lugar(reporte, "edificios.json"), _edificio)
    traslados = _traslados(_lista(crudos, "traslados", reporte), reporte)
    secciones = _indexar(_lista(crudos, "secciones", reporte), "id", _Lugar(reporte, "secciones.json"), _seccion)
    estudiantes = _indexar(_lista(crudos, "estudiantes", reporte), "id", _Lugar(reporte, "estudiantes.json"), _estudiante)
    configuracion = _configuracion(crudos.get("config"), reporte)

    instancia = Instancia(materias, profesores, edificios, traslados, secciones, estudiantes, configuracion)
    validar_coherencia(instancia, reporte)
    return (instancia if reporte.es_valido else None), reporte


def cargar_instancia(crudos: dict[str, Any]) -> Instancia:
    """Como `construir_instancia`, pero lanza `DatosInvalidos` si hay errores."""
    instancia, reporte = construir_instancia(crudos)
    if instancia is None:
        raise DatosInvalidos(reporte)
    return instancia
