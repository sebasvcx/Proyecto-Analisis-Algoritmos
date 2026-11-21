# Caso con respuesta conocida (Sección 7.1, tipo 2)

Generado con `python -m asignador conocidos --semilla 7 --estudiantes 12 --materias 6 --guardar ../data/ejemplos/respuesta-conocida`.

Primero se armaron horarios válidos para los 12 estudiantes a la vez y de ellos
salieron las solicitudes; `respuesta_conocida.json` guarda esa asignación
(estudiante → materia → sección). Demuestra que **todas** las materias pedidas
caben, así que su vector C5..C1 es el máximo posible. Los cupos de las
secciones usadas son exactos y hay secciones señuelo con un solo cupo.

```bash
cd backend
python -m asignador --datos ../data/ejemplos/respuesta-conocida ejecutar --nivel 10
```
