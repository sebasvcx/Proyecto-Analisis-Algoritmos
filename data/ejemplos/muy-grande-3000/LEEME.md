# Escala: 3.000 estudiantes, 500 secciones

Generado con:

```bash
cd backend
python -m asignador --datos ../data/ejemplos/muy-grande-3000 generar --estudiantes 3000 --secciones 500 --escasez ajustada --semilla 42
```

| Nivel | Cobertura | Violaciones | Tiempo del algoritmo |
|---|---|---|---|
| N4 | 96,6 % | 0 | 0,3 s |
| N10 | 99,5 % | 0 | 4,6 s |

Para mostrar que escala casi lineal. **Ojo:** en la web la comparación entre
niveles con esta instancia tarda unos 25 s (corre las 12 variantes); para la
demo basta ejecutar N4 y N10 por separado.

```bash
./ejemplo.sh muy-grande-3000
```
