import type { Dia, Estudiante } from "../api/tipos";

export const DIAS: Dia[] = ["L", "M", "X", "J", "V", "S"];
export const NOMBRE_DIA: Record<Dia, string> = { L: "Lun", M: "Mar", X: "Mié", J: "Jue", V: "Vie", S: "Sáb" };

export const HORA_APERTURA = 7 * 60;
export const HORA_CIERRE = 20 * 60;

export function aMinutos(hora: string): number {
  const [h, m] = hora.split(":").map(Number);
  return h * 60 + m;
}

export function porcentaje(valor: number | null | undefined, decimales = 0): string {
  if (valor === null || valor === undefined) return "—";
  return `${(valor * 100).toFixed(decimales)} %`;
}

export function numero(valor: number): string {
  return Number.isInteger(valor) ? String(valor) : valor.toFixed(1).replace(".", ",");
}

export function fechaCorta(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function trabaja(estudiante: Estudiante): boolean {
  return (estudiante.franjas_libres ?? []).some((f) => (f.tipo ?? "obligatoria") === "obligatoria");
}
