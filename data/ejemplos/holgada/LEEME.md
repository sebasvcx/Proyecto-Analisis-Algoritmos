# Cupos holgados (250 estudiantes, 96 secciones)

Generado con:

```bash
cd backend
python -m asignador --datos ../data/ejemplos/holgada generar --estudiantes 250 --secciones 96 --escasez holgada --semilla 42
```

Sobran cupos: aquí N10 se luce, porque hay espacio para mover estudiantes.

| Método | Cobertura | Violaciones |
|---|---|---|
| N1 | 90,5 % | 97 |
| N3 | 87,5 % | 0 |
| N4 | 89,0 % | 0 |
| N9 | 93,7 % | 0 |
| **N10** | **95,8 %** | 0 |
| Aleatoria | 91,8 % | 0 |
| Llegada | 89,5 % | 0 |

Comparar con `escasa`: los mismos estudiantes y secciones, solo cambian los
cupos.

```bash
./ejemplo.sh holgada
```
