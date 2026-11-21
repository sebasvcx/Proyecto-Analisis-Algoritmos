import type { CriterioSatisfaccion } from "../../api/tipos";
import { porcentaje } from "../../utilidades/formato";
import { CRITERIOS } from "../preferencias/Importancia";

export interface ValorMostrado {
  valor: number | null;
  /** false: el criterio no se pudo evaluar (sin datos) y no entra al promedio. */
  evaluable: boolean;
  peso?: number;
}

const PESO: Record<number, string> = { 0: "nada", 1: "baja", 2: "media", 3: "alta" };

/** Barras de 0 a 100 % por criterio (Sección 5.5). Los no evaluables se muestran apagados. */
export function SatisfaccionPorCriterio({ criterios }: { criterios: Record<CriterioSatisfaccion, ValorMostrado> }) {
  return (
    <div className="barras">
      {CRITERIOS.map((c) => {
        const { valor, evaluable, peso } = criterios[c.clave];
        return (
          <div key={c.clave} className="barra-dato" title={evaluable ? c.ayuda : "Sin información para evaluarlo: no cuenta en el promedio"}>
            <span>
              {c.texto}
              {peso !== undefined && <span className="nivel__marca"> · {PESO[peso]}</span>}
            </span>
            <div className="barra-dato__pista">
              {evaluable && valor !== null && <div className="barra-dato__relleno" style={{ width: `${valor * 100}%` }} />}
            </div>
            <span className="barra-dato__valor" style={{ color: evaluable ? undefined : "var(--gris-500)", fontWeight: evaluable ? undefined : 400 }}>
              {evaluable ? porcentaje(valor) : "no aplica"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
