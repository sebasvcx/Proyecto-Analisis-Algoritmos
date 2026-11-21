// Tipos que reflejan los JSON de data/ y las respuestas del servidor.

export type Dia = "L" | "M" | "X" | "J" | "V" | "S";
export type Entidad = "materias" | "profesores" | "edificios" | "traslados" | "secciones" | "estudiantes" | "config";

export interface Materia {
  codigo: string;
  nombre: string;
  creditos: number;
  semestre: number;
}

export interface Profesor {
  id: string;
  nombre: string;
  departamento?: string;
}

export interface Sesion {
  dia: Dia;
  inicio: string;
  fin: string;
  edificio: string;
  salon: string;
}

export interface Seccion {
  id: string;
  materia: string;
  profesor: string;
  cupo: number;
  sesiones: Sesion[];
}

export interface FranjaJson {
  dia: Dia | "*";
  inicio: string;
  fin: string;
  tipo?: "obligatoria" | "deseable";
}

export interface SolicitudJson {
  codigo: string;
  prioridad: number;
  sustitutas?: string[];
}

export interface Estudiante {
  id: string;
  nombre: string;
  semestre: number;
  materias: SolicitudJson[];
  franjas_libres?: FranjaJson[];
  franjas_preferidas?: FranjaJson[];
  franjas_evitadas?: FranjaJson[];
  profesores?: { id: string; afinidad?: number; veto?: boolean }[];
  social?: { estudiante: string; afinidad: number }[];
  importancia?: Record<string, "alta" | "media" | "baja" | "ninguna">;
}

export interface Configuracion {
  max_creditos?: number;
  valor_sustituta?: number;
  desempate_semestre?: boolean;
  semilla?: number;
  max_cambios?: number;
}

export interface Problema {
  archivo: string;
  registro: string;
  campo: string;
  mensaje: string;
  gravedad: "error" | "advertencia";
}

export interface ResumenDatos {
  archivos: { entidad: Entidad; archivo: string; opcional: boolean; presente: boolean; registros: number | null }[];
  validacion: { errores: number; advertencias: number; problemas: Problema[] };
  configuracion: Configuracion;
}

export type Escasez = "holgada" | "ajustada" | "escasa";

export interface ParametrosGeneracion {
  estudiantes: number;
  secciones: number;
  porcentaje_trabaja: number;
  escasez: Escasez;
  semilla: number;
}

export interface Nivel {
  numero: number;
  nombre: string;
  descripcion: string;
  disponible: boolean;
  reglas: string[];
}

export type EstadoSolicitud = "principal" | "sustituida" | "no_inscrita";

export interface ResultadoSolicitud {
  materia: string;
  prioridad: number;
  estado: EstadoSolicitud;
  seccion: string | null;
  materia_inscrita: string | null;
}

export interface Aviso {
  materia: string;
  causa: string;
  sugerencia: string;
  causas: string[];
  sustituta: string | null;
}

/** Criterios de la Sección 5.5; las claves coinciden con "importancia" en estudiantes.json. */
export type CriterioSatisfaccion = "profesores" | "horario" | "cercania" | "huecos" | "social";

export interface ValorCriterio {
  /** Entre 0 y 1; si no es evaluable vale 0.5 (neutro) y no entra al total. */
  valor: number;
  evaluable: boolean;
  /** Importancia: alta 3, media 2, baja 1, ninguna 0. */
  peso: number;
}

export interface SatisfaccionEstudiante {
  /** Promedio ponderado de los criterios evaluables con peso > 0; 0.5 si no hay ninguno. */
  total: number;
  /** Tiene algún criterio evaluable con peso positivo (solo estos entran al promedio y mínimo). */
  evaluable: boolean;
  criterios: Record<CriterioSatisfaccion, ValorCriterio>;
}

export interface ResumenSatisfaccion {
  estudiantes_evaluables: number;
  promedio: number | null;
  minimo: number | null;
  /** Promedio de cada criterio entre los estudiantes donde es evaluable. */
  por_criterio: Record<CriterioSatisfaccion, number | null>;
}

export interface ResultadoEstudiante {
  id: string;
  creditos: number;
  solicitudes: ResultadoSolicitud[];
  avisos: Aviso[];
  satisfaccion: SatisfaccionEstudiante;
}

export interface Violacion {
  regla: string;
  estudiante: string;
  detalle: string;
  seccion: string | null;
}

export interface Salida {
  corrida: {
    id: string;
    fecha: string;
    nivel: number;
    nombre_nivel: string;
    reglas_del_nivel: string[];
    version: string;
    configuracion: Configuracion;
    tiempo_algoritmo_s: number;
    tiempo_verificacion_s: number;
    estudiantes: number;
    secciones: number;
    /** Solo en las asignaciones de comparación. */
    referencia?: TipoReferencia;
    /** Solo en N10: estadísticas de la mejora local; null en los demás niveles. */
    mejora: {
      cambios_examinados: number;
      cambios_aceptados: number;
      pasadas: number;
      limite_alcanzado: boolean;
    } | null;
  };
  resumen: {
    puntaje_lexicografico: number[];
    por_prioridad: { prioridad: number; pedidas: number; puntaje: number }[];
    solicitudes: { total: number; principales: number; sustituidas: number; pendientes: number };
    cobertura: number | null;
    indicador_academico: number | null;
    satisfaccion: ResumenSatisfaccion;
    /** Q completo (Sección 5.4), en orden de importancia para comparar corridas. */
    objetivo: {
      /** C5..C1 */
      c: number[];
      /** J5..J1; null si el desempate por semestre está desactivado. */
      j: number[] | null;
      /** Suma de la satisfacción de todos los estudiantes. */
      satisfaccion: number;
      /** Suma de posiciones de las sustitutas inscritas (la primera de la lista cuenta 1); menor es mejor. */
      posiciones_sustitutas: number;
    };
  };
  verificacion: {
    reglas_verificadas: string[];
    total: number;
    por_regla: Record<string, number>;
    violaciones: Violacion[];
  };
  estudiantes: ResultadoEstudiante[];
  secciones: { id: string; materia: string; cupo: number; inscritos: number }[];
}

export type TipoReferencia = "aleatoria" | "llegada";

export interface CorridaResumida {
  id: string;
  fecha: string;
  nivel: number;
  nombre_nivel: string;
  estudiantes: number;
  cobertura: number | null;
  violaciones: number;
  /** Solo en las asignaciones de comparación (Sección 7.3). */
  referencia: TipoReferencia | null;
  desempate_semestre: boolean;
}

/** Qué ejecutar: un nivel del algoritmo o una asignación de referencia. */
export interface PeticionCorrida {
  nivel?: number;
  desempate_semestre?: boolean;
  referencia?: TipoReferencia;
  semilla_referencia?: number;
}

/** Una fila de la comparación entre niveles (POST /api/comparacion). */
export interface FilaComparacion {
  metodo: string;
  etiqueta: string;
  cobertura: number | null;
  indicador_academico: number | null;
  c5: number;
  c4: number;
  c3: number;
  c2: number;
  c1: number;
  principales: number;
  sustituidas: number;
  pendientes: number;
  satisfaccion_promedio: number | null;
  satisfaccion_minima: number | null;
  violaciones: number;
  tiempo_algoritmo_s: number;
}

export interface RespuestaGuardarEstudiante {
  estudiante: Estudiante;
  creado: boolean;
  advertencias: Problema[];
}
