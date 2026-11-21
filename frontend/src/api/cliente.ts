import type {
  CorridaResumida,
  Entidad,
  Estudiante,
  FilaComparacion,
  Materia,
  Nivel,
  ParametrosGeneracion,
  PeticionCorrida,
  Profesor,
  RespuestaGuardarEstudiante,
  ResumenDatos,
  Salida,
  Seccion,
} from "./tipos";

export class ErrorApi extends Error {
  constructor(
    message: string,
    readonly estado: number,
    readonly detalle?: unknown,
  ) {
    super(message);
  }
}

export const SIN_SERVIDOR =
  "No se pudo contactar al servidor. Verifique que el backend esté corriendo (uvicorn api.main:app en el puerto 8000).";

async function pedir<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(ruta, {
      ...opciones,
      headers: { "Content-Type": "application/json", ...opciones.headers },
    });
  } catch {
    throw new ErrorApi(SIN_SERVIDOR, 0);
  }
  const cuerpo = await respuesta.json().catch(() => null);
  // El proxy de Vite responde 5xx sin cuerpo JSON cuando el backend está apagado
  if (respuesta.status >= 500 && cuerpo === null) throw new ErrorApi(SIN_SERVIDOR, respuesta.status);
  if (!respuesta.ok) {
    const detalle = cuerpo?.detail;
    const mensaje = typeof detalle === "string" ? detalle : (detalle?.mensaje ?? `Error ${respuesta.status}`);
    throw new ErrorApi(mensaje, respuesta.status, detalle);
  }
  return cuerpo as T;
}

const json = (cuerpo: unknown): RequestInit => ({ body: JSON.stringify(cuerpo) });

export const api = {
  salud: () => pedir<{ estado: string; version: string }>("/api/salud"),
  resumenDatos: () => pedir<ResumenDatos>("/api/datos"),
  leer: <T>(entidad: Entidad) => pedir<T>(`/api/datos/${entidad}`),
  materias: () => pedir<Materia[]>("/api/datos/materias"),
  profesores: () => pedir<Profesor[]>("/api/datos/profesores"),
  secciones: () => pedir<Seccion[]>("/api/datos/secciones"),
  estudiantes: () => pedir<Estudiante[]>("/api/datos/estudiantes"),
  reemplazar: (entidad: Entidad, contenido: unknown) =>
    pedir<ResumenDatos>(`/api/datos/${entidad}`, { method: "PUT", ...json(contenido) }),
  generar: (parametros: ParametrosGeneracion) =>
    pedir<ResumenDatos & { respaldo: string | null }>("/api/datos/generar", { method: "POST", ...json(parametros) }),

  niveles: () => pedir<Nivel[]>("/api/niveles"),
  corridas: () => pedir<CorridaResumida[]>("/api/corridas"),
  corrida: (id: string) => pedir<Salida>(`/api/corridas/${encodeURIComponent(id)}`),
  entradaCorrida: <T>(id: string, entidad: Entidad) =>
    pedir<T>(`/api/corridas/${encodeURIComponent(id)}/entrada/${entidad}`),
  ejecutar: (peticion: PeticionCorrida) => pedir<Salida>("/api/corridas", { method: "POST", ...json(peticion) }),
  comparacion: () => pedir<FilaComparacion[]>("/api/comparacion", { method: "POST" }),
  guardarEstudiante: (estudiante: Estudiante) =>
    pedir<RespuestaGuardarEstudiante>(`/api/estudiantes/${encodeURIComponent(estudiante.id)}`, {
      method: "PUT",
      ...json(estudiante),
    }),
};
