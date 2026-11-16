# Plan de trabajo — entrega final (semana 17)

Cada paso es un commit. Receta por paso: **pruebas primero** (ejemplos de la Tabla 4 y de la tabla de
casos de aceptación del documento) → implementación → regla en el verificador → correr **todas** las
pruebas (incluidas las de niveles anteriores).

Estado: `[x]` hecho · `[ ]` pendiente. Responsable entre paréntesis cuando se reparta.

## Fase 0 — Entorno
- [x] 1. Python 3.12 (`py install 3.12`), `backend/.venv`, `dev.ps1` para Windows, README en UTF-8.
- [x] 2. Solver exacto: **fuerza bruta** sobre combinaciones válidas (sin OR-Tools; en Windows con
  Control inteligente de aplicaciones se bloquean las DLL de numpy que necesita CP-SAT).

## Fase 1 — Reglas obligatorias completas (R1–R9)
- [x] 3. **N3 — Traslados (R8).** Caminata ≤ minutos libres entre sesiones consecutivas + 10.
  Regla en `reglas.py` + verificador. Pruebas: edificios a 10 vs 11 min; hueco de 1 h → 70 min.
- [ ] 4. **N4 — Sustitutas (R9) y avisos.** Probar sustitutas en orden si la principal no cabe;
  `posicion_sustituta`, aviso "sustituida", una sustituta común no atiende dos solicitudes.
  Verificador R9 + aporte 0,8 en métricas. → *Primer punto seguro de entrega.*

## Fase 2 — Satisfacción (N5–N9)
- [ ] 5. **`satisfaccion.py`** con los 5 criterios de la Sec. 5.5, pesos 3/2/1/0 y valores por defecto,
  criterios no evaluables, neutro 0,5. Pruebas unitarias por criterio. Promedio y mínimo en métricas.
- [ ] 6. Elegir "la sección válida de mayor satisfacción" con los criterios activos del nivel:
  - [ ] N5 profesores
  - [ ] N6 horario, franjas deseables y huecos
  - [ ] N7 cercanía entre salones
  - [ ] N8 importancia personal (antes: pesos por defecto)
  - [ ] N9 compañeros

## Fase 3 — N10, mejora global
- [ ] 7. Comparación completa Q: J5..J1 (semestre, si está activo) → satisfacción → suma de posiciones
  de sustitutas → desempate por códigos. Pruebas: semestre 2 vs 8; prioridad 5 siempre gana a 4.
- [ ] 8. Mejora local: mover a un estudiante a una sección equivalente para liberar cupo; aceptar solo
  si Q mejora; límite `max_cambios`. Causa "Cedida por prioridad". Prueba: ejemplo N10 de la Tabla 4.

## Fase 4 — Evaluación (Sección 7 del documento)
- [ ] 9. Generador de casos con respuesta conocida (tipo 2).
- [ ] 10. Solver exacto (fuerza bruta) para 2–6 estudiantes; comparar N10 con el óptimo.
- [ ] 11. Líneas base: asignación aleatoria válida y por orden de llegada.
- [ ] 12. Script de experimentos: 20/200/500/2000 estudiantes × holgada/ajustada/escasa × semillas 0–9
  → CSV con mediana y rango.
- [ ] 13. Pruebas del verificador con salidas con errores intencionales (cupo, duplicados, R8, R9).

## Fase 5 — Web
- [ ] 14. Página **Preferencias** (materias, prioridades, sustitutas, franjas, profesores, compañeros).
- [ ] 15. Ejecutar: casilla de desempate por semestre en N10. Resultados: satisfacción por criterio y
  comparación entre niveles. Horario: sustituciones. Descargar la salida.

## Fase 6 — Cierre
- [ ] 16. Análisis de complejidad del voraz y de la mejora local.
- [ ] 17. Actualizar el documento LaTeX (implementación, resultados, limitaciones) y el README.
- [ ] 18. Preparar la sustentación individual: todos deben entender todos los niveles.

## Prioridades
Imprescindible: Fases 1–3. Muy importante: Fase 4 y paso 16. Si alcanza: Fase 5 y Docker.
Fases 4–5 pueden avanzar en paralelo con 2–3 (uno en el algoritmo, otro en la web/evaluación).
