// Conversión entre las franjas del JSON y una semana editable por celdas de una hora.

import type { Dia, Estudiante, FranjaJson } from "../api/tipos";
import { DIAS, HORA_APERTURA, HORA_CIERRE, aMinutos } from "./formato";

export type TipoFranja = "obligatoria" | "deseable" | "preferida" | "evitada";

/** clave "L-7" (día y hora de inicio de la celda) → tipo */
export type Semana = Map<string, TipoFranja>;

export const HORAS_SEMANA = Array.from({ length: (HORA_CIERRE - HORA_APERTURA) / 60 }, (_, i) => HORA_APERTURA / 60 + i);

export const clave = (dia: Dia, hora: number) => `${dia}-${hora}`;

// Si dos tipos caen en la misma celda gana el más restrictivo
const PRECEDENCIA: TipoFranja[] = ["preferida", "evitada", "deseable", "obligatoria"];

function marcar(semana: Semana, franja: FranjaJson, tipo: TipoFranja) {
  const dias: Dia[] = franja.dia === "*" ? DIAS : [franja.dia];
  for (const dia of dias) {
    for (let m = aMinutos(franja.inicio); m < aMinutos(franja.fin); m += 60) {
      const k = clave(dia, m / 60);
      const previo = semana.get(k);
      if (!previo || PRECEDENCIA.indexOf(tipo) > PRECEDENCIA.indexOf(previo)) semana.set(k, tipo);
    }
  }
}

export function semanaDesde(estudiante: Estudiante): Semana {
  const semana: Semana = new Map();
  for (const f of estudiante.franjas_preferidas ?? []) marcar(semana, f, "preferida");
  for (const f of estudiante.franjas_evitadas ?? []) marcar(semana, f, "evitada");
  for (const f of estudiante.franjas_libres ?? []) marcar(semana, f, f.tipo === "deseable" ? "deseable" : "obligatoria");
  return semana;
}

const hora = (h: number) => `${String(h).padStart(2, "0")}:00`;

/** Une horas seguidas del mismo tipo en franjas; si un tramo se repite los seis días, se escribe con día "*". */
function franjasDe(semana: Semana, tipo: TipoFranja): FranjaJson[] {
  const tramosPorDia = new Map<Dia, string[]>();
  for (const dia of DIAS) {
    const tramos: string[] = [];
    let inicio: number | null = null;
    for (const h of [...HORAS_SEMANA, HORA_CIERRE / 60]) {
      const marcada = h < HORA_CIERRE / 60 && semana.get(clave(dia, h)) === tipo;
      if (marcada && inicio === null) inicio = h;
      if (!marcada && inicio !== null) {
        tramos.push(`${inicio}-${h}`);
        inicio = null;
      }
    }
    tramosPorDia.set(dia, tramos);
  }
  const comunes = (tramosPorDia.get("L") ?? []).filter((t) => DIAS.every((d) => tramosPorDia.get(d)!.includes(t)));
  const franja = (dia: Dia | "*", tramo: string): FranjaJson => {
    const [i, f] = tramo.split("-").map(Number);
    return { dia, inicio: hora(i), fin: hora(f) };
  };
  return [
    ...comunes.map((t) => franja("*", t)),
    ...DIAS.flatMap((d) => tramosPorDia.get(d)!.filter((t) => !comunes.includes(t)).map((t) => franja(d, t))),
  ];
}

/** Devuelve el estudiante con sus franjas reescritas desde la semana (las listas vacías se omiten). */
export function aplicarSemana(estudiante: Estudiante, semana: Semana): Estudiante {
  const libres = [
    ...franjasDe(semana, "obligatoria").map((f) => ({ ...f, tipo: "obligatoria" as const })),
    ...franjasDe(semana, "deseable").map((f) => ({ ...f, tipo: "deseable" as const })),
  ];
  const preferidas = franjasDe(semana, "preferida");
  const evitadas = franjasDe(semana, "evitada");
  const { franjas_libres: _l, franjas_preferidas: _p, franjas_evitadas: _e, ...resto } = estudiante;
  return {
    ...resto,
    ...(libres.length ? { franjas_libres: libres } : {}),
    ...(preferidas.length ? { franjas_preferidas: preferidas } : {}),
    ...(evitadas.length ? { franjas_evitadas: evitadas } : {}),
  };
}
