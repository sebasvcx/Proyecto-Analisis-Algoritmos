# Plan de trabajo — entrega final (semana 17)

Cada paso es un commit. Receta por paso: **pruebas primero** (ejemplos de la Tabla 4 y de la tabla de
casos de aceptación del documento) → implementación → regla en el verificador → correr **todas** las
pruebas (incluidas las de niveles anteriores).

Estado: `[x]` hecho · `[ ]` pendiente. Responsable entre paréntesis.

## Reparto

- **Sebastián — algoritmo:** pasos 5–8 y 10. Son secuenciales y tocan los mismos archivos
  (`voraz.py`, `niveles.py`), así que los hace una sola persona.
- **Andrés — evaluación y web:** pasos 9, 11, 12, 13, 14 y 15. Solo usan la salida del algoritmo
  (`ejecutar_corrida`), no su implementación; no tocar `backend/asignador/algoritmo/`.
- Cada uno en su rama. Acordar pronto el **formato JSON de la satisfacción** (paso 5), porque la
  parte de satisfacción del paso 15 depende de él.
- Fase 6: cada uno escribe la complejidad y la sección del documento de su parte; al final, repasar
  juntos todo el código para la sustentación individual.

## Fase 0 — Entorno
- [x] 1. Python 3.12 (`py install 3.12`), `backend/.venv`, `dev.ps1` para Windows, README en UTF-8. (Sebastián)
- [x] 2. Solver exacto: **fuerza bruta** sobre combinaciones válidas (sin OR-Tools; en Windows con
  Control inteligente de aplicaciones se bloquean las DLL de numpy que necesita CP-SAT). (Sebastián)

## Fase 1 — Reglas obligatorias completas (R1–R9)
- [x] 3. **N3 — Traslados (R8).** Caminata ≤ minutos libres entre sesiones consecutivas + 10.
  Regla en `reglas.py` + verificador. Pruebas: edificios a 10 vs 11 min; hueco de 1 h → 70 min. (Sebastián)
- [x] 4. **N4 — Sustitutas (R9) y avisos.** Probar sustitutas en orden si la principal no cabe;
  `posicion_sustituta`, aviso "sustituida", una sustituta común no atiende dos solicitudes.
  Verificador R9 + aporte 0,8 en métricas. → *Primer punto seguro de entrega.* (Sebastián)

## Fase 2 — Satisfacción (N5–N9)
- [x] 5. **`satisfaccion.py`** con los 5 criterios de la Sec. 5.5, pesos 3/2/1/0 y valores por defecto,
  criterios no evaluables, neutro 0,5. Pruebas unitarias por criterio. Promedio y mínimo en métricas.
  Fijar el formato JSON de la satisfacción en la salida. (Sebastián)
  → Formato fijado en `frontend/src/api/tipos.ts` (`SatisfaccionEstudiante`, `ResumenSatisfaccion`):
  cada estudiante trae `satisfaccion`, y `resumen.satisfaccion` trae promedio, mínimo y `por_criterio`.
- [x] 6. Elegir "la sección válida de mayor satisfacción" con los criterios activos del nivel: (Sebastián)
  - [x] N5 profesores
  - [x] N6 horario, franjas deseables y huecos
  - [x] N7 cercanía entre salones
  - [x] N8 importancia personal (antes: pesos por defecto)
  - [x] N9 compañeros (cuenta también la satisfacción de quienes tienen afinidad hacia el estudiante)
  - **Decisión a documentar en el informe (paso 17):** antes que la satisfacción, se minimiza la pérdida
    en las solicitudes pendientes del mismo estudiante (prioridad 5→1), para que una comodidad no cueste
    una materia (Sec. 5.4, Tabla 5 "Preferencias"). Esto subió la cobertura de 85,6 % (N4) a 88,2 % (N5)
    con los datos reales.

## Fase 3 — N10, mejora global
- [x] 7. Comparación completa Q: J5..J1 (semestre, si está activo) → satisfacción → suma de posiciones
  de sustitutas → desempate por códigos. Pruebas: semestre 2 vs 8; prioridad 5 siempre gana a 4. (Sebastián)
  → `asignador/objetivo.py` (`Registro`, `puntuar`, `comparar`, `criterio_decisivo`); `resumen.objetivo`
  en la salida. La primera sustituta de la lista cuenta 1 en la suma de posiciones (documentarlo).
- [x] 8. Mejora local: mover a un estudiante a una sección equivalente para liberar cupo; aceptar solo
  si Q mejora; límite `max_cambios`. Causa "Cedida por prioridad". Prueba: ejemplo N10 de la Tabla 4.
  Debe recuperar las principales que N4 pierde frente a N3 por sustitutas que ocupan cupos. (Sebastián)
  → `algoritmo/mejora.py`. Datos reales: cobertura 89,2 % (N9) → 93,2 % (N10), 84 cambios aceptados.
  **Para el informe (limitaciones):** con cupos escasos no mejora nada (mover a alguien exige una sección
  alternativa con cupo; no hay intercambios entre dos estudiantes); con 2.000 estudiantes y cupos
  holgados el límite de 10.000 cambios se agota en la primera pasada. Q se evalúa de forma incremental.
  Los avisos de N10 se regeneran con el horario final; "Limitación del algoritmo" si algo cabía y no se tomó.

## Fase 4 — Evaluación (Sección 7 del documento)
- [x] 9. Generador de casos con respuesta conocida (tipo 2). (Andrés)
  → `generador/conocidos.py` (horarios válidos plantados → solicitudes; cupos justos + señuelos),
  `comparacion_conocida.py`, comando `python -m asignador conocidos --casos 40`. Ejemplo en
  `data/ejemplos/respuesta-conocida/`. **Resultado (40 casos, 30 est.):** respuesta plantada válida en 40/40;
  N10 atiende 98,7 % (mín. 95,5 %), nunca pierde prioridad 5 ni 4; N3/N4 91,3 %.
- [x] 10. Solver exacto (fuerza bruta) para 2–6 estudiantes; comparar N10 con el óptimo. Requiere el paso 7. (Sebastián)
  → `asignador/exacto.py` (búsqueda exhaustiva con poda segura por C), `generador/pequenos.py`,
  `comparacion_exacta.py`, comando `python -m asignador exacto --casos 300`.
  **Resultado (300 instancias):** N10 igual de bueno que el óptimo en 61 % (sin semestre) y 67,7 % (con
  semestre); cuando pierde: 77 por satisfacción y 40 por materias (C). **Para el informe:** las pérdidas
  en C vienen de cadenas de 3+ cambios (p. ej. semilla 145: e01 cambia de sección, eso libera un cupo para
  e02, que reacomoda su propia materia para que otra deje de chocar); la mejora local solo hace 1–2 pasos.
  Se corrigió `metricas.puntaje`: sumaba la satisfacción redondeada a 4 decimales.
- [x] 11. Líneas base: asignación aleatoria válida y por orden de llegada. (Andrés)
  → `asignador/referencias.py` (mismas reglas que N10, con sustitutas; sin preferencias ni mejora; solo
  importa de `algoritmo/`). `corrida.armar_salida` se separó de `ejecutar_corrida` para reutilizarla.
  CLI `python -m asignador referencia --tipo aleatoria|llegada`; API `POST /api/corridas {"referencia": ...}`.
- [x] 12. Script de experimentos: 20/200/500/2000 estudiantes × holgada/ajustada/escasa × semillas 0–9
  → CSV con mediana y rango. Hoy puede correr con N4 y luego cambiar a N10. (Andrés)
  → `asignador/experimentos.py` + `backend/scripts/experimentos.py` (crudo.csv, resumen.csv, meta.json).
  Resumen copiado en `docs/ProyectoAlgoritmos/datos/`. 480 corridas en ~3,5 min, 0 violaciones.
- [x] 13. Pruebas del verificador con salidas con errores intencionales (cupo, duplicados, R8, R9). (Andrés)
  → `tests/test_verificador.py`. **Se encontró y corrigió un hueco:** un estudiante repetido en la salida no
  se detectaba (ahora es error de estructura "E").

## Fase 5 — Web
- [x] 14. Página **Preferencias** (materias, prioridades, sustitutas, franjas, profesores, compañeros). (Andrés)
  → `/estudiantes/:id/preferencias` (también crea estudiantes nuevos). Guarda con `PUT /api/estudiantes/{id}`,
  que valida antes de escribir y devuelve errores por campo (el lector ahora indica `materias[0].prioridad`).
- [x] 15. Ejecutar: casilla de desempate por semestre en N10. Resultados: satisfacción por criterio y
  comparación entre niveles. Horario: sustituciones. Descargar la salida. (Andrés)
  → Casilla solo para esa corrida (no cambia config.json); referencias ejecutables desde la web;
  `POST /api/comparacion` (aleatoria, llegada, N1–N10 sin guardar); "Mi satisfacción" en el horario.

## Fase 6 — Cierre
- [x] 16. Análisis de complejidad del voraz y de la mejora local. (Sebastián; Andrés: líneas base ✓)
  → `docs/ProyectoAlgoritmos/complejidad.tex` (N1–N4, N5–N9, N10, verificador, solver exacto, memoria y
  mediciones). Mediciones reproducibles con `backend/scripts/medir_complejidad.py`. Falta incluirlo en
  `sn-article.tex` (paso 17) y que Andrés agregue la complejidad de sus líneas base.
- [ ] 17. Actualizar el documento LaTeX (implementación, resultados, limitaciones) y el README. (ambos, cada uno su parte)
  - [x] Parte de Sebastián: título, resumen e introducción; tabla de causas (+2) y de tecnología;
    secciones nuevas `implementacion.tex`, `resultados.tex`, `complejidad.tex` y Conclusiones; README.
  - [x] Parte de Andrés: buscar las notas en **rojo** y los `% TODO (Andrés)` en `resultados.tex`
    (asignaciones de referencia y experimentos), `interfaz.tex` (app implementada y capturas) y en
    Conclusiones de `sn-article.tex`.
  - [ ] Compilar en Overleaf y revisar que la tabla de resultados por nivel no se salga del margen.
- [ ] 18. Preparar la sustentación individual: todos deben entender todos los niveles. (ambos)

## Prioridades
Imprescindible: Fases 1–3. Muy importante: Fase 4 y paso 16. Si alcanza: Fase 5 y Docker.
