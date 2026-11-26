# Escala: 1.000 estudiantes, 200 secciones

Generado con:

```bash
cd backend
python -m asignador --datos ../data/ejemplos/grande-1000 generar --estudiantes 1000 --secciones 200 --escasez ajustada --semilla 42
```

| Método | Cobertura | Violaciones | Tiempo |
|---|---|---|---|
| N1 | 93,0 % | 361 | |
| N4 | 92,0 % | 0 | |
| N9 | 95,1 % | 0 | |
| **N10** | **99,0 %** | 0 | ~1 s |
| Aleatoria | 95,1 % | 0 | |
| Llegada | 94,5 % | 0 | |

En la web la corrida de N10 tarda alrededor de 1 s; la **comparación entre
niveles** (corre las 12 variantes) unos 4 s.

```bash
./ejemplo.sh grande-1000
```
