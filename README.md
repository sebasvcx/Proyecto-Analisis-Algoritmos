# Asignación de horarios estudiantiles

Proyecto de Análisis de Algoritmos 2026-30 (Pontificia Universidad Javeriana).
El diseño, la formalización y la estrategia de datos están en `docs/ProyectoAlgoritmos/sn-article.tex`;

## Estructura

```
backend/
  asignador/            algoritmo (paquete Python independiente de la web)
    dominio/            TADs: Franja, Sesión, Sección, Estudiante, Solicitud, Preferencias…
    datos/              lectura de los JSON, validación de precondiciones, respaldos
    algoritmo/          TAD Horario, reglas R1–R9, catálogo de niveles, asignación voraz
    generador/          instancias sintéticas reproducibles por semilla
    verificador.py      recalcula las reglas sobre la salida sin reutilizar el algoritmo
    metricas.py         puntaje lexicográfico (C5…C1), cobertura, indicador académico
    corrida.py          asignar → serializar → verificar → guardar en resultados/
  api/                  servidor FastAPI (lee/escribe data/, lanza corridas)
  tests/                pruebas por nivel, lector, verificador, generador y API
frontend/               React + TypeScript (Vite)
data/                   instancia actual en JSON (fuente de verdad)
  ejemplos/             casos pequeños con respuesta conocida
resultados/             salidas de cada corrida (se generan, no se versionan)
```

## Puesta en marcha

Requisitos: **Python 3.12** (3.11–3.13 funcionan; 3.14+ aún no tiene ruedas
precompiladas para algunas dependencias) y Node 20+.

En Windows, con el Python Install Manager: `py install 3.12`.

La web **necesita el backend corriendo**: si solo se levanta Vite, las
peticiones a `/api` fallan con `ECONNREFUSED` y la página muestra "El servidor
no responde". La forma más simple es levantar ambos con un solo comando
(instala dependencias la primera vez; Ctrl+C detiene los dos):

```bash
./dev.sh                                                # Linux / macOS
powershell -ExecutionPolicy Bypass -File .\dev.ps1      # Windows
```

O por separado, en dos terminales:

```bash
# Backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: py -V:3.12 -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
pytest                                   # pruebas
uvicorn api.main:app --reload            # API en http://localhost:8000 (docs en /docs)

# Frontend (otra terminal)
cd frontend
npm install
npm run dev                              # http://localhost:5173 (redirige /api al backend)
```

## Línea de comandos

```bash
cd backend
python -m asignador generar --estudiantes 250 --secciones 96 --escasez ajustada --semilla 42
python -m asignador validar
python -m asignador ejecutar --nivel 10
python -m asignador exacto --casos 200 --nivel 10   # compara con la solución exacta en instancias pequeñas
```

## Estado de los niveles

| Nivel | Qué agrega | Estado |
|---|---|---|
| N1 | Prioridad, choques y cupos (R1–R4) | Implementado |
| N2 | Créditos, franjas obligatorias y vetos (R5–R7) | Implementado |
| N3 | Traslado entre edificios (R8) | Implementado |
| N4 | Sustitutas (R9) y avisos | Implementado |
| N5–N9 | Elección por satisfacción: profesores, horario y huecos, cercanía, importancia, compañeros | Implementado |
| N10 | Desempate por semestre y mejora local | Implementado |
