# Ejemplos preparados

Cada carpeta es una instancia completa (los siete JSON) con un `LEEME.md` que
explica qué muestra y qué resultado esperar. Todos se comprobaron con N1–N10,
las dos referencias, la API y las 323 pruebas.

| Carpeta | Tamaño | Para mostrar |
|---|---|---|
| `demo` | 8 est., 8 secc. | **El principal**: cada estudiante muestra una regla o un nivel (R6, R7, R8, sustituta, N5, N10, semestre) |
| `preferencias` | 9 est., 16 secc. | N5 a N9: qué sección elige cada criterio de satisfacción (profesor, horario, huecos, cercanía, importancia, amigos) |
| `avisos` | 9 est., 14 secc. | Todos los avisos: cupo lleno, choque, tope de créditos, franja obligatoria, profesor vetado, traslado, sin secciones, materia ya inscrita y cedida por prioridad |
| `caso-semestre` | 2 est., 1 secc. | Desempate por semestre en su forma más simple |
| `respuesta-conocida` | 12 est. | Se sabe que cabe todo: N2–N9 se quedan en 92,7 % y N10 llega al 100 % |
| `errores` | 8 est. | Validación: cinco errores a propósito, la web se niega a ejecutar |
| `pequena` | 40 est., 42 secc. | Generada; la aleatoria tiene más cobertura que N10 y aun así N10 es mejor (orden Q) |
| `escasa` | 250 est., 96 secc. | Cupos escasos: misma cobertura, pero N10 atiende mucha más prioridad 5 |
| `holgada` | 250 est., 96 secc. | Cupos holgados: N10 llega al 95,8 % |
| `grande-1000` | 1.000 est., 200 secc. | Escala: N10 99 % en ~1 s |
| `muy-grande-3000` | 3.000 est., 500 secc. | Escala: N10 en ~5 s (la comparación entre niveles tarda ~25 s) |
| `../` (`data/`) | 250 est., 96 secc. | La instancia oficial de la entrega |

## Usarlos sin dañar nada

Desde la raíz del repositorio:

```bash
./ejemplo.sh                 # lista los ejemplos
./ejemplo.sh preferencias    # copia el ejemplo a $TMPDIR/asignador/vivo y arranca la web
./ejemplo.sh oficial         # lo mismo con data/
```

El script trabaja sobre una **copia**: lo que se guarde desde la web y las
corridas quedan en `$TMPDIR/asignador/`. Cada vez que se ejecuta empieza de
cero. Para cambiar de ejemplo: Ctrl+C y `./ejemplo.sh <otro>`.

Para editar los JSON de la copia: `code "$TMPDIR/asignador/vivo"` u
`open "$TMPDIR/asignador/vivo"`. Para borrarla: `rm -rf "$TMPDIR/asignador"`.

Por consola, sin la web (desde `backend/`, con el venv activo):

```bash
python -m asignador --datos ../data/ejemplos/avisos validar
python -m asignador --datos ../data/ejemplos/avisos ejecutar --nivel 4 --resultados "$TMPDIR/res"
python -m asignador --datos ../data/ejemplos/avisos referencia --tipo aleatoria --resultados "$TMPDIR/res"
```

`ejecutar` y `referencia` solo **leen** la carpeta de datos; la corrida se
guarda en `--resultados`.

## Crear uno nuevo en vivo

```bash
cd backend
mkdir -p "$TMPDIR/nuevo"
python -m asignador --datos "$TMPDIR/nuevo" generar --estudiantes 500 --secciones 120 --escasez ajustada --semilla 5
python -m asignador --datos "$TMPDIR/nuevo" ejecutar --nivel 10 --resultados "$TMPDIR/res"
```

Mínimo 42 secciones (una por materia del catálogo del generador). `--escasez`
puede ser `holgada`, `ajustada` o `escasa`.
