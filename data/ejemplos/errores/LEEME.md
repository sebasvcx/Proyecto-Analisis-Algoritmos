# Errores: datos inválidos a propósito

Copia del caso `demo` con cinco errores puestos a mano, para mostrar la
validación. La web marca los archivos en rojo y **se niega a ejecutar**
(responde 422); por consola, `validar` imprime:

```
[error] secciones.json › ALG-01 › sesiones[0]: las horas deben ser en punto
[error] estudiantes.json › e01 › materias[1].prioridad: el valor 7 debe estar entre 1 y 5
[error] estudiantes.json › e04 › semestre: el valor 12 debe estar entre 1 y 10
[error] estudiantes.json › e07 › id: identificador repetido 'e07'
[error] secciones.json › BD-01 › profesor: el profesor 'P99' no existe
[error] estudiantes.json › e05 › social: el estudiante 'e04' no existe
```

El último aparece porque e04 quedó inválido (semestre 12) y e05 lo nombra como
amigo: un error arrastra al otro. Al corregir el semestre desaparecen los dos.

Cómo usarlo en vivo: cargarlo, mostrar los mensajes (archivo › registro ›
campo), corregir uno en el JSON, recargar y ver que el mensaje desaparece.

| Error | Dónde | Corrección |
|---|---|---|
| Hora no en punto | `secciones.json`, ALG-01, primera sesión `"inicio": "07:30"` | `"07:00"` |
| Prioridad 7 | `estudiantes.json`, e01, segunda materia | `3` |
| Semestre 12 | `estudiantes.json`, e04 | `3` |
| Id repetido | `estudiantes.json`, el último estudiante dice `"e07"` | `"e08"` |
| Profesor inexistente | `secciones.json`, BD-01 `"profesor": "P99"` | `"P6"` |

```bash
./ejemplo.sh errores
```
