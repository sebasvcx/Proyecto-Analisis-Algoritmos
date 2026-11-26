# Preferencias: qué agrega cada nivel de N5 a N9 (9 estudiantes)

Todos los cupos sobran (5 por sección), así que **todos entran en todos los
niveles** (cobertura 100 %). Lo único que cambia es **qué sección** recibe cada
uno: cada estudiante tiene dos secciones válidas que solo se diferencian en un
criterio de satisfacción, y cada nivel activa uno nuevo.

Hasta N4 siempre se toma la primera sección válida (la de menor id, "-01").

| Estudiante | Pide | Preferencia | Cambia en | De → a |
|---|---|---|---|---|
| e01 Andrea | HIS p4 | afinidad +2 con P2 (HIS-02) | **N5** (profesores) | HIS-01 → HIS-02 |
| e02 Bruno | LIT p4 | prefiere clases de 14:00 a 20:00 | **N6** (horario) | LIT-01 (M 07–09) → LIT-02 (M 15–17) |
| e03 Camila | ALG p5, FIS p4 | ninguna: menos huecos | **N6** (huecos) | FIS-01 (X 15–17, hueco de 6 h) → FIS-02 (X 09–11, seguida) |
| e04 David | MAT p5, QUI p4 | ninguna: menos caminata | **N7** (cercanía) | QUI-01 (edificio C, 9 min) → QUI-02 (edificio A) |
| e05 Eva | ECO p4 | +2 con P1 (mañana) y prefiere la tarde; importancia: profesores **alta**, horario **baja** | **N5**, **N6** y **N8** | N5 ECO-01 (profesor) · N6–N7 ECO-02 (con pesos por defecto gana el horario) · **N8** ECO-01 (con su importancia gana el profesor) |
| e06 Fabio | BIO p3 | amigo de e07 (+2) | **N9** (compañeros) | BIO-01 → BIO-02 (con Gabriela) |
| e07 Gabriela | BIO p5 | trabaja S 07–09 (obligatoria) | N2 (R6) | BIO-01 (viola R6 en N1) → BIO-02 |
| e08 Héctor | ART p3 | quiere evitar a e09 (−2) | **N9** (compañeros) | ART-01 (con Irene) → ART-02 |
| e09 Irene | ART p5 | ninguna | — | ART-01 siempre |

Resumen: N1 tiene 1 violación (R6 de e07) y desde N2, 0. N10 da lo mismo que N9
porque ya no hay nada que mejorar.

Qué decir: «una comodidad nunca le quita una materia a nadie: aquí todos entran
igual; los niveles 5 a 9 solo eligen **mejor** entre secciones que ya eran
válidas». El caso de Eva muestra que N8 respeta lo que el estudiante declaró
importante en vez de los pesos por defecto (profesores 2, horario 2, cercanía 2,
huecos 1, compañeros 2).

```bash
./ejemplo.sh preferencias        # desde la raíz del repo
```
