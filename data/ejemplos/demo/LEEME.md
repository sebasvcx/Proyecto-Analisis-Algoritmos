# Caso de demostración (8 estudiantes)

Caso pequeño hecho a mano para la sustentación: cada estudiante muestra una
regla o un nivel distinto, así que al ejecutar N1, N2, N3, N4, N5 y N10 se ve
exactamente qué agrega cada uno. Todo lo de abajo se comprobó ejecutándolo.

## Oferta

| Sección | Materia (créditos) | Profesor | Cupo | Horario | Edificio |
|---|---|---|---|---|---|
| ALG-01 | Álgebra (3) | P1 Rojas | 2 | L y X 07–09 | A |
| BD-01 | Bases de datos (3) | P6 Ruiz | **1** | L y X 14–16 | B |
| CAL-01 | Cálculo (4) | P1 Rojas | **1** | L y X 09–11 | A |
| CAL-02 | Cálculo (4) | P2 Díaz | **1** | M y J 07–09 | B |
| ETI-01 | Ética (2) | P5 Vega | 3 | V 07–09 | A |
| FIS-01 | Física (4) | P3 Mora | 2 | L y X 09–11 | **C** |
| FIS-02 | Física (4) | P6 Ruiz | 3 | M y J 11–13 | B |
| PRG-01 | Programación (3) | P4 León | **1** | M y J 09–11 | A |

Caminata: A↔B 5 min, **A↔C 15 min**, B↔C 8 min. Entre dos clases seguidas hay
10 min (cada clase termina 10 min antes), así que de A a C **no** se alcanza.

## Estudiantes y qué muestra cada uno

| Estudiante | Pide | Qué muestra |
|---|---|---|
| e01 Ana (sem. 2) | CAL p5, PRG p3 (sustituta ETI) | Sustituta desde N4; en N10 la mueven de CAL-01 a CAL-02 |
| e02 Bruno (sem. 8) | CAL p5; trabaja M y J 07–11 (obligatoria) | R6 en N1 (le dan CAL-02 encima del trabajo); N2–N9 sin CAL; **N10 se la consigue** |
| e03 Carla (sem. 4) | PRG p5 | Prioridad: le gana PRG-01 (cupo 1) a Ana, que la pidió con p3 |
| e04 Diego (sem. 3) | ALG p5, FIS p4 | R8: en N1–N2 queda ALG (A) → FIS-01 (C) seguidas; desde N3 pasa a FIS-02 |
| e05 Elena (sem. 3) | FIS p3; afinidad +2 con P6; amiga de e04 | N5: elige FIS-02 (profesor P6) en vez de FIS-01 |
| e06 Felipe (sem. 6) | FIS p4; **veta** a P3 | R7: en N1 le dan FIS-01 (de P3); desde N2, FIS-02 |
| e07 Gina (sem. 1) | BD p5 | Empate con e08 por BD-01 (cupo 1): gana por código |
| e08 Hugo (sem. 9) | BD p5 | Con desempate por semestre en N10, gana él y Gina recibe "Cedida por prioridad" |

## Resultado esperado por nivel

| Nivel | Cobertura | C5..C1 | Violaciones (verificador) | Qué cambia |
|---|---|---|---|---|
| N1 | 80 % | 5; 2; 1; 0; 0 | 5: R6 ×2 (e02), R7 ×1 (e06), R8 ×2 (e04) | Ignora créditos, franjas, vetos y traslados |
| N2 | 70 % | 4; 2; 1; 0; 0 | 2: R8 ×2 (e04) | e02 pierde CAL; e06 pasa a FIS-02 |
| N3 | 70 % | 4; 2; 1; 0; 0 | 0 | e04 pasa a FIS-02 |
| N4 | 80 % | 4; 2; 1,8; 0; 0 | 0 | e01 recibe ETI como sustituta de PRG |
| N5–N9 | 80 % | 4; 2; 1,8; 0; 0 | 0 | e05 cambia a FIS-02 por su afinidad con P6 |
| N10 | **90 %** | **5**; 2; 1,8; 0; 0 | 0 | e01 → CAL-02 y e02 entra a CAL-01 |
| N10 + semestre | 90 % | 5; 2; 1,8; 0; 0 | 0 | BD-01 pasa de e07 a e08 ("Cedida por prioridad") |

## Cómo ejecutarlo

En la web (sin tocar `data/`):

```bash
ASIGNADOR_DATOS="$PWD/data/ejemplos/demo" ./dev.sh          # macOS / Linux, desde la raíz
```

```powershell
$env:ASIGNADOR_DATOS = "$PWD\data\ejemplos\demo"; .\dev.ps1   # Windows, desde la raíz
```

Por consola:

```bash
cd backend
python -m asignador --datos ../data/ejemplos/demo ejecutar --nivel 1
python -m asignador --datos ../data/ejemplos/demo ejecutar --nivel 10
```

Ojo: con `ASIGNADOR_DATOS` apuntando aquí, lo que se guarde desde la web se
escribe en **esta** carpeta. Para volver al estado original:
`git checkout -- data/ejemplos/demo`.
