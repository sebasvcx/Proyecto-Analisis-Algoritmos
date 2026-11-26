# AGENTS.md

Proyecto final de Análisis de Algoritmos 2026-30 (PUJ): asignación de horarios estudiantiles.
Entrega final: semana 17 (implementación + sustentación individual). Todo el código, comentarios,
commits y textos de la UI van **en español**.

## Fuente de verdad del diseño

- Enunciado: `docs/enunciado_2026_30.pdf`.
- Documento de diseño (entrega semana 10): `docs/ProyectoAlgoritmos/sn-article.tex` + `formalizacion.tex`,
  `estrategia-datos.tex`, `interfaz.tex`. La implementación **debe seguir esta formalización**
  (el enunciado exige que el algoritmo final salga del diseño entregado). Ante dudas, citar la sección.
- Puntos clave del diseño:
  - Reglas obligatorias R1–R9 (Tabla 1) y preferencias P1–P10 (Tabla 2).
  - Orden de comparación Q: vector lexicográfico (C5..C1) con principal=1, sustituta=0,8 →
    desempate por semestre J5..J1 (solo si `desempate_semestre`) → suma de satisfacción →
    menor suma de posiciones de sustitutas → registros (estudiante, solicitud, sección) ordenados.
  - Traslado (R8): caminata ≤ minutos libres entre sesiones consecutivas + 10. Clases seguidas → 10 min.
  - Satisfacción (Sec. 5.5): criterios profesores, horario, cercanía, huecos (÷4680), compañeros;
    pesos alta/media/baja/ninguna = 3/2/1/0, por defecto 2 (huecos 1); no evaluables se excluyen; sin
    ninguno → 0,5.
  - Niveles **acumulativos** N1–N10 (Tabla 4); cada nivel con pruebas propias y debe pasar las anteriores.
  - Casos de aceptación: Tabla `tab:aceptacion` en `estrategia-datos.tex`.

## Estructura

```
backend/asignador/   algoritmo puro (sin dependencias de la web)
  dominio/           TADs inmutables (modelos.py, tiempo.py: Franja)
  datos/             lectura JSON, validación de precondiciones, respaldos
  algoritmo/         horario.py (TAD Horario + Contexto con inscritos), reglas.py (R2..R7 como objetos Regla),
                     niveles.py (catálogo NIVELES, flag `disponible`), voraz.py, causas.py
  generador/         instancias sintéticas por semilla
  verificador.py     recalcula reglas sobre la SALIDA serializada, sin reutilizar código del algoritmo
  metricas.py        Q (C5..C1), cobertura, indicador académico
  corrida.py         asignar → serializar → verificar → medir → guardar en resultados/
backend/api/         FastAPI (rutas/datos.py, rutas/corridas.py)
backend/tests/       pytest; fixture `correr` en conftest.py, constructores en constructores.py
frontend/            React 18 + TS + Vite; páginas en src/paginas/
data/                instancia actual (JSON); data/ejemplos/ casos pequeños
```

## Comandos

```bash
cd backend && .venv/Scripts/python -m pytest -q                       # pruebas
cd backend && .venv/Scripts/python -m uvicorn api.main:app --reload   # API :8000
cd frontend && npm run dev                                            # web :5173 (proxy /api → :8000)
cd frontend && npm run typecheck
cd backend && .venv/Scripts/python -m asignador ejecutar --nivel 2
powershell -ExecutionPolicy Bypass -File .\dev.ps1                    # ambos (Windows); dev.sh en Linux/macOS
```

Entorno: **Python 3.12** en `backend/.venv` (el `python` global es 3.15 y rompe dependencias).
No usar numpy/pandas/ortools: el Control inteligente de aplicaciones de Windows bloquea sus DLL;
el solver exacto será por fuerza bruta.

## Plan

Seguir [PLAN.md](PLAN.md) paso a paso y marcar las casillas al terminar cada paso.

## Estado (al 2026-11-16)

- Hecho: N1–N10 (R1–R9, sustitutas, elección por satisfacción en `algoritmo/eleccion.py`, mejora local
  y desempate por semestre en `algoritmo/mejora.py`), verificador
  R1–R9, métricas Q/cobertura, satisfacción (`asignador/satisfaccion.py`, en la salida y el resumen),
  generador, API, páginas web Datos, Estudiantes, Ejecutar, Resultados, Horario.
- Desde N5, `Elector` ordena las secciones válidas por: (1) menor pérdida en las solicitudes pendientes
  del estudiante, de prioridad 5 a 1; (2) mayor satisfacción con los criterios del nivel; (3) menor id.
  Las candidatas se miden inscribiéndolas provisionalmente (agregar/quitar del TAD Horario).
- Solver exacto independiente en `asignador/exacto.py` (reglas con código propio); comparación con N10 en
  `comparacion_exacta.py` y `python -m asignador exacto`. `metricas.puntaje` recalcula la satisfacción sin
  redondear (la de la salida está a 4 decimales).
- Q completo (Sec. 5.4) en `asignador/objetivo.py`: se calcula desde una lista de `Registro`; las
  métricas los sacan de la salida (`metricas.registros_de_salida`). `Puntaje.clave()`: menor = mejor.
- El verificador revisa todas sus reglas en cualquier nivel; las que el nivel no cubre se muestran
  como "no aplica" en la web. Las pruebas de "cero violaciones" usan el nivel más alto disponible.
- Pendiente: ver [PLAN.md](PLAN.md) (siguiente de Sebastián: paso 18, preparar la sustentación). Documento: no hay LaTeX local, compilan en
  Overleaf; las partes pendientes de Andrés están marcadas en rojo y con `% TODO (Andrés)`.. Reparto: Sebastián hace
  el algoritmo; Andrés (compañero) evaluación y web, sin tocar `asignador/algoritmo/`.

## Convenciones

- Para agregar un nivel: nuevas `Regla` en `reglas.py`, entrada en `NIVELES` con `disponible=True`,
  lógica en `voraz.py` (o módulo nuevo), regla correspondiente en `verificador.py` y `tests/test_nivelN.py`.
- El verificador NO debe importar de `asignador.algoritmo`.
- Determinismo: ordenar siempre por códigos; reordenar registros de entrada no debe cambiar el resultado.
- Commits estilo conventional en español: `feat(algoritmo): ...`, `test(...)`, `docs: ...`.
