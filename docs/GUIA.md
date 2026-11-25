# Guía rápida del proyecto y de la sustentación

Resumen de lo importante: cómo funciona el algoritmo, qué hace cada parte del
backend y de la web, cómo preparar la sustentación (demostración,
modificaciones en vivo y preguntas) y cómo resolver los errores típicos.
El detalle formal está en el informe (`docs/ProyectoAlgoritmos/`, sección 10
"Algoritmo implementado").

---

## 1. El problema en una frase

Dada una oferta de secciones (materia, profesor, horario, salón, cupo) y las
solicitudes de los estudiantes (materias con prioridad 1–5, sustitutas y
preferencias), asignar a cada uno una sección por materia **sin violar nunca
R1–R9** y, dentro de eso, atender primero lo más prioritario y después las
preferencias.

| Regla | Qué prohíbe | Desde |
|---|---|---|
| R1 | Inscribir algo que no se pidió (ni es sustituta) | N1 |
| R2 | Dos secciones de la misma materia | N1 |
| R3 | Clases que se cruzan | N1 |
| R4 | Pasar el cupo | N1 |
| R5 | Pasar el tope de créditos (20) | N2 |
| R6 | Clase en una franja "no disponible" (obligatoria) | N2 |
| R7 | Profesor vetado | N2 |
| R8 | Clases seguidas en edificios sin tiempo de caminar (hay 10 min + el hueco) | N3 |
| R9 | Sustituta inscrita si la principal quedó | N4 |

**Cómo se decide qué resultado es mejor (orden Q, lexicográfico):**
1. `(C5, C4, C3, C2, C1)`: por cada prioridad, principales × 1 + sustitutas × 0,8. Gana la primera posición distinta.
2. `(J5..J1)`: lo mismo multiplicado por el semestre (solo si `desempate_semestre` está activo).
3. Mayor suma de satisfacción.
4. Menor suma de posiciones de sustitutas (la 1.ª cuenta 1).
5. Lista de registros por códigos (desempate final determinista).

Consecuencia clave: **una comodidad nunca compensa perder una materia**, y una
materia de prioridad 5 vale más que cualquier cantidad de prioridad 4.

---

## 2. El algoritmo (lo que hay que saber explicar)

```
leer JSON → validar → ORDENAR solicitudes → VORAZ (N1–N9) → [N10: BÚSQUEDA LOCAL] → avisos → salida → VERIFICADOR → métricas
```

### 2.1 Orden de atención (`algoritmo/voraz.py::orden_de_atencion`)
Todas las solicitudes de todos los estudiantes, ordenadas por
`(-prioridad, -semestre si N10 con desempate, id estudiante, código materia)`.
Por eso el resultado **no depende del orden del JSON** (hay una prueba que
baraja los archivos: `tests/test_nivel1.py::test_reordenar_registros_no_cambia_el_resultado`).

### 2.2 Voraz (N1–N9, `voraz.py`)
Para cada solicitud en ese orden:
- recorre las secciones de la materia (por id) y pregunta `Horario.puede_agregar(sección, reglas_del_nivel)`, que devuelve **la lista de causas** por las que no cabe (vacía = cabe);
- **N1–N4:** toma la primera válida;
- **N5–N9:** toma la mejor válida según `eleccion.Elector` (ver 2.3);
- **N4+:** si la principal no cabe, prueba las sustitutas en orden (heredan la prioridad);
- si no queda nada, genera un **aviso** con la causa más frecuente (empate → menor número de regla) y todas las demás.

Nunca deshace una decisión → rápido, pero no óptimo.

### 2.3 Elección entre secciones válidas (N5–N9, `eleccion.py`)
Entre las válidas elige por, en orden:
1. **Mirar adelante:** la que menos daño hace a las solicitudes que al mismo estudiante le faltan (si una se queda sin sección pierde 1; si solo cabría como sustituta, 0,2), de prioridad 5 a 1.
2. **Satisfacción** con los criterios del nivel: N5 profesores, N6 + horario y huecos, N7 + cercanía, N8 usa la importancia declarada (alta 3, media 2, baja 1, ninguna 0; antes pesos por defecto), N9 + compañeros (y suma la satisfacción de quien tiene afinidad hacia él).
3. Menor id de sección.

Cada candidata se mide con **prueba y deshacer**: `agregar` → medir → `quitar`.

### 2.4 Búsqueda local (N10, `algoritmo/mejora.py`)
Parte del voraz de N9 (con desempate por semestre si está activo) y hace
pasadas con dos movimientos:
1. **Insertar con desplazamiento:** una solicitud no atendida por su principal intenta entrar; si la sección solo está llena, mueve a un ocupante a otra sección de la misma materia con cupo.
2. **Reubicar:** cambiar una inscripción a otra sección de la misma materia.

Acepta un cambio **solo si Q mejora estrictamente** (si no, lo deshace).
Termina porque Q solo sube y hay finitas asignaciones; además hay un tope
`max_cambios` (10.000). Q se evalúa **de forma incremental**: solo los
estudiantes que cambian y quienes tienen afinidad hacia ellos.
Al final rehace los avisos con el horario definitivo.

### 2.5 Lo que NO es el algoritmo pero lo respalda
| Archivo | Para qué |
|---|---|
| `verificador.py` | Recalcula R1–R9 sobre la **salida guardada**, sin reutilizar código del algoritmo |
| `exacto.py` | Óptimo por vuelta atrás con poda (solo 2–6 estudiantes) para comparar |
| `referencias.py` | Aleatoria válida y por orden de llegada (líneas base) |
| `generador/` | Instancias por semilla; `conocidos.py` planta una respuesta que atiende el 100 % |
| `satisfaccion.py` | 5 criterios en [0,1]; no evaluable si no hay datos; promedio ponderado |
| `objetivo.py` | El orden Q (`Puntaje.clave()`: menor = mejor) |

### 2.6 Estrategias (pregunta segura)
| Estrategia | Dónde |
|---|---|
| Ordenamiento previo | `voraz.py` (orden de atención) |
| Voraz por prioridad | `voraz.py`, N1–N9 |
| Voraz con mirada adelante + prueba/deshacer | `eleccion.py`, N5–N9 |
| Búsqueda local (ascenso por primera mejora) con evaluación incremental | `mejora.py`, N10 |
| Vuelta atrás con ramificación y poda | `exacto.py` (evaluación) |
| Aleatorización (Fisher–Yates) y construcción inversa | `referencias.py`, `generador/` |

### 2.7 Complejidad (chuleta)
Notación: E estudiantes, S secciones, R solicitudes (≤ r·E), σ secciones por
materia, β sustitutas por solicitud, c cupo, M = max_cambios, c_R costo de
comprobar reglas (O(r log r + f) con sesiones acotadas).

| Parte | Tiempo | Con parámetros por estudiante acotados |
|---|---|---|
| N1–N4 | O(R log R + R·σ(1+β)·c_R) | **O(E log E)** (domina ordenar) |
| N5–N9 | O(R log R + R[(1+β)²·r·σ²·c_R + (1+β)σ(1+I)c_S]) | O(E log E), **cuadrático en σ** |
| N10 | O(T_N9 + Π·R(1+β)σ²c(r+c_R) + M·c_P), Π ≤ M+1 | casi lineal; la mejora la acota M |
| Referencias | O(R·σ(1+β)·c_R) | O(E) |
| Verificador | O(E((rq)² + rqf) + S) | O(E + S) |
| Exacto | O(b^R ·(…)), b = σ(1+β)+1 | **exponencial** |
| Memoria | O(S + R) | |

Medido: N4 y N9 con exponente ≈ 1,05 respecto a E (lineal); N10 1,27 porque
también crecen los cambios examinados hasta tocar M.
Script: `python scripts/medir_complejidad.py`.

---

## 3. Backend (FastAPI + paquete `asignador`)

```
backend/asignador/
  dominio/       TADs inmutables (Franja, Sesión, Sección, Estudiante, Solicitud, Preferencias)
  datos/         lector y validación de los JSON (errores con archivo › registro › campo)
  algoritmo/     horario.py (TAD Horario), reglas.py (R2–R8), niveles.py (catálogo N1–N10),
                 voraz.py, eleccion.py, mejora.py, causas.py
  corrida.py     ejecutar_corrida: asignar → serializar → verificar → métricas → guardar
backend/api/     main.py, rutas/datos.py, rutas/estudiantes.py, rutas/corridas.py
```

- **Un nivel = lista de reglas + banderas** (`niveles.py`): `sustitutas`, `criterios`, `pesos_declarados`, `mejora`. Para agregar una regla se crea en `reglas.py` y se incluye en los niveles.
- **La API lee los JSON en cada petición** (sin caché): si se edita un archivo a mano, basta con volver a ejecutar.
- Endpoints: `GET/PUT /api/datos/{entidad}`, `POST /api/datos/generar`, `PUT /api/estudiantes/{id}` (valida antes de escribir), `POST /api/corridas` (`{"nivel": 10, "desempate_semestre": true}` o `{"referencia": "aleatoria"}`), `GET /api/corridas[/{id}]`, `POST /api/comparacion` (referencias + N1–N10 sin guardar). Documentación interactiva: http://localhost:8000/docs
- Variables de entorno: `ASIGNADOR_DATOS` (carpeta de datos, por defecto `data/`), `ASIGNADOR_RESULTADOS`, `ASIGNADOR_RESPALDOS`, `ASIGNADOR_CORS`.

### Línea de comandos (desde `backend/`)
```bash
python -m asignador validar                                  # revisa los JSON
python -m asignador ejecutar --nivel 10                      # corrida sobre data/
python -m asignador --datos ../data/ejemplos/demo ejecutar --nivel 4
python -m asignador referencia --tipo aleatoria|llegada
python -m asignador exacto --casos 300 --nivel 10            # N10 vs óptimo
python -m asignador conocidos --casos 40 --nivel 10          # N10 vs respuesta plantada
python -m asignador generar --estudiantes 250 --secciones 96 --escasez ajustada --semilla 42
python scripts/experimentos.py                               # 480 corridas, ~3,5 min
python scripts/medir_complejidad.py
pytest -q                                                    # 323 pruebas
```

---

## 4. Frontend (React + TypeScript + Vite)

| Página (ruta) | Qué mostrar | Archivo |
|---|---|---|
| Datos (`/datos`) | Archivos cargados y validación, importar JSON, generar instancia por semilla | `paginas/Datos.tsx` |
| Estudiantes (`/estudiantes`) | Lista con búsqueda, **+ Nuevo estudiante** | `paginas/Estudiantes.tsx` |
| Preferencias (`/estudiantes/:id/preferencias`) | Materias/prioridad/sustitutas, semana pintable (no disponible, deseable, preferida, evitar), profesores (afinidad y veto), compañeros, importancia. Guardar valida en el servidor | `paginas/Preferencias.tsx`, `componentes/preferencias/` |
| Ejecutar (`/ejecutar`) | Elegir nivel o referencia, casilla de desempate (solo esa corrida), **tope de créditos y desempate por defecto** (escriben `config.json`) | `paginas/Ejecutar.tsx` |
| Resultados (`/resultados`) | Cobertura, C5..C1, satisfacción por criterio, verificador por regla, cambios de N10, **comparación entre niveles**, descargar JSON | `paginas/Resultados.tsx` |
| Horario (`/resultados/:id`) | Grilla semanal, sustituciones, avisos con causa y sugerencia, "Mi satisfacción" | `paginas/Horario.tsx` |

`api/cliente.ts` habla con `/api` (Vite redirige al puerto 8000); `api/tipos.ts`
tiene los tipos de la salida; `estado/ContextoApp.tsx` guarda la corrida actual.

---

## 5. Preparar la sustentación (15 min: 5 demo + 5 modificaciones + 5 preguntas)

### 5.1 Antes de llegar (checklist)
- [ ] `git pull` y `./dev.sh` (o `dev.ps1`) arranca sin errores en **el computador que se va a llevar**; probarlo sin internet (las dependencias ya instaladas).
- [ ] `cd backend && pytest -q` → 323 pasan.
- [ ] Abrir http://localhost:5173 y http://localhost:8000/docs.
- [ ] Tener abiertos en el editor: `voraz.py`, `eleccion.py`, `mejora.py`, `reglas.py`, `niveles.py` y `data/ejemplos/demo/*.json`.
- [ ] Tener el PDF del informe abierto en la sección 10.
- [ ] Copia de seguridad: `git stash`/`git checkout -- data/` deja todo como estaba si algo se daña en vivo.

### 5.2 Ejemplos preparados
1. **`data/ejemplos/demo/`** (8 estudiantes, hecho para la demo). Cada estudiante muestra una regla o nivel; la tabla "resultado esperado por nivel" está en su `LEEME.md`. Resumen: N1 80 % con 5 violaciones (R6, R7, R8) → N2 70 % → N3 0 violaciones → N4 entra una sustituta → N5 cambia a e05 de sección por su profesor favorito → **N10 90 %** (mueve a Ana para que Bruno, que trabaja, entre a Cálculo) → con desempate por semestre, BD pasa de Gina (sem. 1) a Hugo (sem. 9).
2. **`data/` (250 estudiantes)** para mostrar escala y la comparación entre niveles: N10 93,2 % vs N9 89,2 % vs referencias ~86 %, 0 violaciones.
3. **`data/ejemplos/caso-semestre/`** (2 estudiantes, 1 cupo) para el desempate por semestre.
4. **`data/ejemplos/respuesta-conocida/`** (12 estudiantes, se sabe que cabe todo).

Levantar la web sobre el ejemplo demo (desde la raíz del repo):
```bash
ASIGNADOR_DATOS="$PWD/data/ejemplos/demo" ./dev.sh
# Windows:  $env:ASIGNADOR_DATOS = "$PWD\data\ejemplos\demo"; .\dev.ps1
```
Para volver a la instancia grande: cerrar (Ctrl+C) y `./dev.sh` sin la variable.

### 5.3 Guion de la demostración (5 min)
1. **(30 s)** Datos: mostrar que cargó, 0 errores; explicar la oferta en una frase (tabla del `LEEME.md`).
2. **(1 min)** Ejecutar **N1** → Resultados: verificador con violaciones R6/R7/R8 "no aplica"; explicar que N1 solo tiene R1–R4.
3. **(1 min)** Ejecutar **N4**: 0 violaciones; abrir el horario de **e01** → sustituta ETI y aviso "Cupo lleno" de PRG (se la ganó e03 con prioridad 5).
4. **(1 min)** Ejecutar **N10**: cobertura 80 % → 90 %, C5 de 4 a 5; abrir **e02** (Bruno): ahora tiene CAL-01; abrir **e01**: la movieron a CAL-02. Mostrar "cambios aceptados" de la mejora.
5. **(1 min)** **Comparación entre niveles** (gráfica/tabla) y, si sobra tiempo, cambiar a la instancia de 250 para mostrar escala.
6. **(30 s)** Marcar desempate por semestre y ejecutar N10: BD pasa a Hugo y Gina recibe "Cedida por prioridad".

### 5.4 Modificaciones en vivo (5 min): qué pueden pedir y cómo hacerlo

Regla general: **cambiar el dato → volver a ejecutar el nivel → abrir Resultados/Horario**. La API relee los archivos en cada corrida, así que también vale editar el JSON a mano y ejecutar de nuevo.

| Les piden… | Cómo (web) | Cómo (archivo) | Qué debería pasar en el demo |
|---|---|---|---|
| Agregar un estudiante | Estudiantes → **+ Nuevo estudiante** → materias, prioridad → Guardar | Añadir un objeto a `estudiantes.json` | `e09` (sem. 10) con PRG p5: empata con e03 y pierde por código ("Cupo lleno"); con desempate por semestre en N10 gana él y e03 recibe "Cedida por prioridad" |
| Quitar un estudiante | — (editar archivo) | Borrar su objeto de `estudiantes.json` (y quitarlo de `social` de otros) | Si se quita e01, Bruno obtiene CAL desde N2 sin necesitar N10 |
| Más / menos cupo | — | `cupo` en `secciones.json` | BD-01 con cupo 2 → e07 y e08 entran, cobertura 100 % en N10 |
| Cambiar prioridad | Preferencias del estudiante | `prioridad` en `estudiantes.json` | Si e01 pide PRG con p5, empata con e03 y gana e01 por código; e03 queda sin PRG ("Cupo lleno") |
| Tope de créditos | Ejecutar → **Tope de créditos por estudiante** | `max_creditos` en `config.json` | Con 6: Diego (ALG 3 + FIS 4) pierde FIS con aviso "Tope de créditos" |
| Franja no disponible (trabajo) | Preferencias → pintar "no disponible" | `franjas_libres` con `"tipo": "obligatoria"` | Bruno sin trabajo los M/J → obtiene CAL-02 desde N2 |
| Vetar un profesor | Preferencias → casilla veto | `"profesores": [{"id": "P3", "veto": true}]` | Ver e06: nunca queda en FIS-01 desde N2 |
| Preferir un profesor | Preferencias → afinidad +2 | `"afinidad": 2` | Ver e05: cambia de sección desde N5 |
| Tiempo de caminata | — | `minutos` en `traslados.json` | A↔C a 8 min → Diego puede quedarse en FIS-01 en N3 |
| Nueva sección | — | Añadir a `secciones.json` (id único, sesiones de 2 h en hora en punto, 07–20) | Una CAL-03 con cupo, en un horario fuera del trabajo de Bruno (p. ej. V 09–11), hace que N2 ya lo atienda |
| Sustituta | Preferencias → sustitutas | `"sustitutas": ["ETI"]` | Solo se usa desde N4; vale 0,8 |
| Activar desempate por semestre | Ejecutar → casilla (solo esa corrida) | `desempate_semestre` en `config.json` | Solo afecta a N10 |
| Más estudiantes en general | Datos → Generar (estudiantes, secciones, escasez, semilla) | `python -m asignador generar …` | **Reemplaza todos los datos** (deja respaldo en `.respaldos/`) |

Restricciones de formato que la validación revisa (si algo sale en rojo, es esto):
sesiones de **2 h** que empiezan en **hora en punto** entre 07:00 y 20:00; días
`L M X J V S` (o `*` = todos); prioridad 1–5; semestre 1–10; créditos 1–6;
afinidad −2..+2; ids únicos; una sustituta no puede ser una materia ya pedida;
nadie puede tener afinidad social consigo mismo.

Antes de cambiar algo, **decir en voz alta qué se espera** usando el orden Q
("como es prioridad 5, debería ganarle a…"); después mostrarlo en el horario y
en el verificador.

### 5.5 Banco de preguntas (5 min)

**¿Qué estrategia usa el algoritmo?** Voraz por prioridad (con ordenamiento
previo y elección con mirada adelante entre secciones válidas) seguido de una
búsqueda local que solo acepta mejoras estrictas del orden Q. Se eligió voraz
porque el objetivo es lexicográfico: atender primero la prioridad 5 asegura que
nada de menor prioridad le quite un cupo.

**¿Es óptimo?** No. Una decisión temprana puede ocupar el cupo que otro
necesitaba (ejemplo demo: Ana toma CAL-01 y Bruno solo podía esa). N10 arregla
cadenas de 1–2 cambios; frente al óptimo exacto es igual de bueno en el 61 % de
300 instancias pequeñas y nunca lo supera. Pierde con cadenas de 3+ cambios.

**¿Por qué no resolverlo exacto?** Problemas cercanos (selección de intervalos
por trabajos) son NP-difíciles; la búsqueda exacta es O(b^R), exponencial en el número
de solicitudes; por eso solo se usa con 2–6 estudiantes.

**¿Por qué termina N10?** Cada cambio aceptado mejora Q estrictamente, así que
nunca se repite una asignación y hay un número finito; además se detiene a los
`max_cambios` examinados.

**¿Complejidad del algoritmo final?** O(E log E) del ordenamiento más trabajo
lineal por solicitud en N1–N9 (cuadrático en σ en el peor caso por la mirada
adelante); N10 suma pasadas O(R·σ²·c) acotadas por M. En la práctica casi
lineal: exponente medido 1,05 (N9) y 1,27 (N10).

**¿De dónde sale el log?** De ordenar las R solicitudes una vez. Las
referencias no ordenan globalmente y son O(E).

**¿Por qué σ²?** En N5–N9, por cada sección candidata (σ) se revisa si las
solicitudes pendientes del estudiante aún caben, probando sus secciones (σ).

**¿Qué es la evaluación incremental?** En N10 no se recalcula Q para los E
estudiantes en cada cambio; solo el aporte de los ≤ 2 que se mueven y la
satisfacción de quienes tienen afinidad hacia ellos. Como Q se compara
componente a componente, comparar esa parte equivale a comparar el total.

**¿Cómo saben que la salida es válida?** El verificador recalcula R1–R9 sobre
el JSON de salida, con código propio; se probó con 15 salidas con errores
puestos a propósito. Ninguna de las 480 corridas de experimentos violó una regla.

**¿Qué pasa con los empates?** Orden fijo: prioridad → (semestre en N10 si está
activo) → id de estudiante → código de materia. Por eso el resultado no
depende del orden de los registros.

**¿Cuánto vale una sustituta y por qué?** 0,8 de una principal
(`valor_sustituta`), dentro de la prioridad de la solicitud: atender con
sustituta es mejor que nada, peor que la principal.

**¿Cómo se calcula la satisfacción?** Cinco criterios entre 0 y 1
(profesores, horario, cercanía, huecos, compañeros); los no evaluables no
cuentan; promedio ponderado por la importancia (alta 3, media 2, baja 1,
ninguna 0).

**¿Qué es R8 exactamente?** Entre dos clases seguidas el tiempo libre es el
hueco + 10 min (cada clase termina 10 min antes). La caminata entre edificios
(`traslados.json`) debe ser ≤ ese tiempo.

**¿Cuánta memoria usa?** O(S + R): inscritos por sección, horarios,
pendientes e índice de ocupantes. La exacta, O(R) de profundidad.

**¿Qué cambió respecto al diseño?** Solución exacta propia en vez de CP-SAT
(DLLs bloqueadas en Windows), dos causas nuevas de aviso ("Materia ya
inscrita", "Limitación del algoritmo"), revisión de pendientes antes de la
satisfacción en N5–N9, sin Docker.

**Limitaciones:** sin intercambios entre dos estudiantes (con cupos escasos N10
no mejora), sin cadenas de 3+ cambios, tope de cambios con 2.000 estudiantes,
y a igual prioridad el voraz favorece al de menor código.

---

## 6. Solución de errores

| Síntoma | Causa | Arreglo |
|---|---|---|
| La web dice "El servidor no responde" / `ECONNREFUSED` en la consola de Vite | El backend no está corriendo | Usar `./dev.sh` o levantar `uvicorn api.main:app --reload` en `backend/` |
| `address already in use` (8000 o 5173) | Quedó un proceso viejo | macOS/Linux: `lsof -ti:8000 \| xargs kill`; Windows: `netstat -ano \| findstr 8000` y `taskkill /PID <pid> /F` |
| `pip install` falla compilando algo | Python demasiado nuevo para alguna dependencia | Usar Python 3.12 (`py install 3.12` en Windows) y recrear `backend/.venv` |
| `ModuleNotFoundError: asignador` / `api` | Se ejecutó fuera de `backend/` o sin el venv | `cd backend && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`) |
| `vite: command not found` | Faltan dependencias del frontend | `cd frontend && npm install` |
| Datos en rojo / corrida rechazada | Un JSON no cumple el formato | Leer el mensaje: dice archivo › registro › campo (`materias[0].prioridad`). Revisar la lista de restricciones de 5.4. `python -m asignador validar` lo muestra en consola |
| Advertencia "demanda supera los cupos" | No es error: hay más solicitudes que cupos | Nada; es esperado en el demo |
| Guardar preferencias dice "No se guardó" | El servidor validó y encontró errores | Corregir los campos marcados; no se escribió nada |
| Se dañaron los datos | Una importación o generación | Restaurar desde `data/.respaldos/` o `git checkout -- data/` |
| N10 tarda mucho (≥ 2.000 estudiantes) | Llega a `max_cambios` | Bajar `max_cambios` en `config.json` o usar la instancia de 250 |
| Cambié un JSON y la web muestra lo viejo | La página no se recargó | Recargar la pestaña y volver a ejecutar (la API no cachea) |
| `exacto` dice "se superaron N nodos" | Instancia demasiado grande para la búsqueda exhaustiva | Es esperado: usarla solo con 2–6 estudiantes |
| Una prueba falla después de un cambio | Se rompió una regla o un nivel anterior | `pytest -q -x` para ver la primera; `pytest tests/test_nivel10.py -q` por nivel |

---

## 7. El informe (LaTeX)

- Fuente: `docs/ProyectoAlgoritmos/sn-article.tex`. Las secciones 1–9 son la
  **primera entrega sin cambios** (salvo una frase en el resumen y la
  introducción que anuncian la sección nueva). La única sección nueva es
  **10 "Algoritmo implementado"** (`algoritmo-implementado.tex`): desarrollo y
  funcionamiento, estrategias y dónde se aplican, complejidad, pruebas y
  resultados, conclusiones.
- PDF compilado: `docs/ProyectoAlgoritmos_Final.pdf`.
- Compilar localmente (macOS): `brew install tectonic` y, desde
  `docs/ProyectoAlgoritmos/`:
  ```bash
  tectonic -X compile sn-article.tex --outdir /tmp/informe
  ```
  En Overleaf: subir la carpeta `docs/ProyectoAlgoritmos/` y compilar con pdfLaTeX.
- Entrega: Campus Virtual, **jueves 26 de noviembre, 11:59 p. m.**
