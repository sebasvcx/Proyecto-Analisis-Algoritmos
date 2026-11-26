# Cupos escasos (250 estudiantes, 96 secciones)

Generado con:

```bash
cd backend
python -m asignador --datos ../data/ejemplos/escasa generar --estudiantes 250 --secciones 96 --escasez escasa --semilla 42
```

Hay muchos menos cupos que solicitudes, así que muchos estudiantes quedan con avisos de "Cupo lleno".

| Método | Cobertura | C5 | C4 | Violaciones |
|---|---|---|---|---|
| N1 | 70,9 % | 284 | 250 | 67 |
| N4 | 70,2 % | 282,6 | 247,2 | 0 |
| N9 | 70,9 % | 284,8 | 255,6 | 0 |
| N10 | 71,2 % | 284,8 | 256,6 | 0 |
| Aleatoria | 70,4 % | **195,4** | 178,2 | 0 |
| Llegada | 70,8 % | 221,6 | 207,8 | 0 |

Con cupos escasos la cobertura casi no cambia entre métodos, pero **a quién**
se atiende sí: N10 cubre casi todas las solicitudes de prioridad 5 (284,8) y la
aleatoria solo 195,4. Aquí se ve por qué atender primero la prioridad alta
importa. También muestra una limitación: con cupos tan escasos N10 casi no
mejora sobre N9, porque no hay a dónde mover a nadie.

```bash
./ejemplo.sh escasa
```
