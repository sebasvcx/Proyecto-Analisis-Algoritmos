"""Catálogo ficticio para generar instancias.

Los códigos y combinaciones de nombres son inventados; no corresponden a
personas ni a la oferta real de ninguna universidad.
"""

# (código, nombre, créditos, semestre sugerido, departamento)
MATERIAS: tuple[tuple[str, str, int, int, str], ...] = (
    ("CAL1", "Cálculo Diferencial", 4, 1, "Matemáticas"),
    ("ALG", "Álgebra Lineal", 3, 1, "Matemáticas"),
    ("PRG1", "Introducción a la Programación", 3, 1, "Sistemas"),
    ("PEN", "Pensamiento Sistémico", 2, 1, "Sistemas"),
    ("CAL2", "Cálculo Integral", 4, 2, "Matemáticas"),
    ("FIS1", "Física Mecánica", 4, 2, "Física"),
    ("PRG2", "Programación Avanzada", 3, 2, "Sistemas"),
    ("LOG", "Lógica y Matemáticas Discretas", 3, 2, "Matemáticas"),
    ("CAL3", "Cálculo Vectorial", 4, 3, "Matemáticas"),
    ("FIS2", "Electricidad y Magnetismo", 4, 3, "Física"),
    ("EST", "Estructuras de Datos", 3, 3, "Sistemas"),
    ("ECD", "Ecuaciones Diferenciales", 3, 3, "Matemáticas"),
    ("PROB", "Probabilidad", 3, 4, "Matemáticas"),
    ("ADA", "Análisis de Algoritmos", 3, 4, "Sistemas"),
    ("BD", "Bases de Datos", 3, 4, "Sistemas"),
    ("ARQ", "Arquitectura de Computadores", 3, 4, "Electrónica"),
    ("ESTI", "Estadística Inferencial", 3, 5, "Matemáticas"),
    ("SO", "Sistemas Operativos", 3, 5, "Sistemas"),
    ("ISW1", "Ingeniería de Software", 3, 5, "Sistemas"),
    ("RED", "Comunicaciones y Redes", 3, 5, "Electrónica"),
    ("ISW2", "Arquitectura de Software", 3, 6, "Sistemas"),
    ("COMP", "Teoría de la Computación", 3, 6, "Sistemas"),
    ("OPT", "Optimización", 3, 6, "Matemáticas"),
    ("ECO", "Fundamentos de Economía", 2, 6, "Economía"),
    ("IA", "Inteligencia Artificial", 3, 7, "Sistemas"),
    ("DIST", "Sistemas Distribuidos", 3, 7, "Sistemas"),
    ("SIM", "Simulación Digital", 3, 7, "Industrial"),
    ("ETI", "Ética Profesional", 2, 7, "Humanidades"),
    ("GPR", "Gerencia de Proyectos", 3, 8, "Industrial"),
    ("SEG", "Seguridad Informática", 3, 8, "Sistemas"),
    ("COMPU", "Computación Gráfica", 3, 8, "Sistemas"),
    ("ML", "Aprendizaje de Máquina", 3, 8, "Sistemas"),
    ("PG1", "Proyecto de Grado I", 2, 9, "Sistemas"),
    ("EMP", "Emprendimiento", 2, 9, "Administración"),
    ("NUB", "Computación en la Nube", 3, 9, "Sistemas"),
    ("DAT", "Ciencia de Datos", 3, 9, "Sistemas"),
    ("PG2", "Proyecto de Grado II", 4, 10, "Sistemas"),
    ("TEO", "Teología", 2, 10, "Humanidades"),
    ("ELEC1", "Electiva de Énfasis I", 3, 10, "Sistemas"),
    ("ELEC2", "Electiva de Énfasis II", 3, 10, "Sistemas"),
    ("FOT", "Fotografía Básica", 1, 10, "Artes"),
    ("DEP", "Deporte Formativo", 1, 10, "Bienestar"),
)

EDIFICIOS: tuple[tuple[str, str, float, float], ...] = (
    # (id, nombre, x, y) en una cuadrícula aproximada del campus, en "minutos de caminata"
    ("A", "Edificio Aulas Norte", 0.0, 0.0),
    ("B", "Edificio de Ingeniería", 3.0, 1.0),
    ("C", "Edificio de Ciencias", 5.0, 4.0),
    ("D", "Biblioteca Central", 2.0, 5.0),
    ("E", "Edificio de Artes", 8.0, 2.0),
    ("F", "Edificio Administrativo", 6.0, 8.0),
    ("G", "Laboratorios", 10.0, 6.0),
    ("H", "Centro Deportivo", 12.0, 11.0),
)

NOMBRES = (
    "Valentina", "Santiago", "Mariana", "Sebastián", "Daniela", "Mateo", "Isabella", "Samuel",
    "Gabriela", "Nicolás", "Sara", "Alejandro", "Laura", "Tomás", "Camila", "Julián",
    "Lucía", "Andrés", "Paula", "Felipe", "Juliana", "David", "Manuela", "Esteban",
    "Natalia", "Simón", "Antonia", "Martín", "Salomé", "Emilio", "Catalina", "Joaquín",
)
APELLIDOS = (
    "Gómez", "Rodríguez", "Martínez", "López", "Herrera", "Castro", "Ramírez", "Torres",
    "Vargas", "Rojas", "Moreno", "Jiménez", "Díaz", "Muñoz", "Ortiz", "Suárez",
    "Mejía", "Restrepo", "Cárdenas", "Pineda", "Salazar", "Quintero", "Ospina", "Arango",
)

# Patrones de días para secciones de dos sesiones semanales
PATRONES_DOS_SESIONES = (("L", "X"), ("M", "J"), ("X", "V"), ("L", "J"), ("M", "V"), ("J", "S"))
DIAS_UNA_SESION = ("L", "M", "X", "J", "V", "S")
