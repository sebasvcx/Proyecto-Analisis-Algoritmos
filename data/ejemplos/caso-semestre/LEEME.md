# Caso pequeño de la Sección 7.1 del documento

Una materia M1 con una sola sección S1 (cupo 1, lunes 07:00–09:00 en B1) y dos
estudiantes que la piden con prioridad 5: e01 (semestre 2) y e02 (semestre 8).

- Desempate por semestre **desactivado** (este `config.json`): S1 queda para e01
  por el desempate final de códigos; e02 recibe un aviso de "Cupo lleno".
- Desempate por semestre **activado** (nivel 10, casilla «desempate por semestre» en Ejecutar): S1 queda para e02 y e01 recibe "Cedida por prioridad".

```bash
cd backend
python -m asignador --datos ../data/ejemplos/caso-semestre ejecutar --nivel 2 --resultados /tmp/res
```
