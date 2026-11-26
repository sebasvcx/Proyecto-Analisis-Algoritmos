# Instancia pequeña generada (40 estudiantes, 42 secciones)

Generado con:

```bash
cd backend
python -m asignador --datos ../data/ejemplos/pequena generar --estudiantes 40 --secciones 42 --escasez ajustada --semilla 11
```

42 secciones es el mínimo del generador (una por cada materia del catálogo).

| Método | Cobertura | C5 | Violaciones |
|---|---|---|---|
| N1 | 83,5 % | 35 | 6 |
| N3 | 80,1 % | 30 | 0 |
| N4 | 83,0 % | 32,4 | 0 |
| N10 | 83,0 % | 32,4 | 0 |
| Aleatoria | **84,7 %** | 29,2 | 0 |
| Llegada | 83,0 % | 32,4 | 0 |

Sirve para una pregunta trampa: **la aleatoria tiene más cobertura que N10, y
aun así N10 es mejor**. El objetivo no es la cobertura sino el orden Q: primero
C5 (prioridad 5). N10 atiende 32,4 de prioridad 5 y la aleatoria 29,2; la
aleatoria "gana" cobertura metiendo materias de prioridad 1 y 2 en el lugar de
las de prioridad 5.

```bash
./ejemplo.sh pequena
```
