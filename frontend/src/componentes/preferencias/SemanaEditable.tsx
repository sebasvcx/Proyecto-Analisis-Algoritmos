import { useEffect, useRef, useState } from "react";
import type { Dia } from "../../api/tipos";
import { DIAS, NOMBRE_DIA } from "../../utilidades/formato";
import { HORAS_SEMANA, clave, type Semana, type TipoFranja } from "../../utilidades/franjas";
import { Segmentado } from "../Tarjeta";

type Pincel = TipoFranja | "borrar";

const PINCELES: { valor: Pincel; texto: string }[] = [
  { valor: "obligatoria", texto: "No disponible" },
  { valor: "deseable", texto: "Libre deseable" },
  { valor: "preferida", texto: "Preferida" },
  { valor: "evitada", texto: "Evitar" },
  { valor: "borrar", texto: "Borrar" },
];

const ETIQUETA: Record<TipoFranja, string> = {
  obligatoria: "No disponible",
  deseable: "Libre deseable",
  preferida: "Preferida",
  evitada: "Evitar",
};

/**
 * Semana de lunes a sábado por horas. Se elige un pincel y se pinta haciendo clic
 * o arrastrando. "No disponible" es una franja obligatoria (regla R6); las demás
 * son preferencias que pueden ceder.
 */
export function SemanaEditable({ semana, alCambiar }: { semana: Semana; alCambiar: (s: Semana) => void }) {
  const [pincel, setPincel] = useState<Pincel>("obligatoria");
  const pintando = useRef(false);

  useEffect(() => {
    const soltar = () => (pintando.current = false);
    window.addEventListener("pointerup", soltar);
    return () => window.removeEventListener("pointerup", soltar);
  }, []);

  const pintar = (dia: Dia, hora: number) => {
    const k = clave(dia, hora);
    const actual = semana.get(k);
    if ((pincel === "borrar" && !actual) || actual === pincel) return;
    const nueva = new Map(semana);
    if (pincel === "borrar") nueva.delete(k);
    else nueva.set(k, pincel);
    alCambiar(nueva);
  };

  return (
    <div>
      <div className="fila-acciones" style={{ marginTop: 0, marginBottom: 12 }}>
        <Segmentado etiqueta="Tipo de franja a marcar" opciones={PINCELES} valor={pincel} alCambiar={setPincel} />
      </div>
      <div className="semana-editable" role="grid" aria-label="Semana: clic o arrastre para marcar franjas">
        <div />
        {DIAS.map((d) => (
          <div key={d} className="semana-editable__dia" role="columnheader">
            {NOMBRE_DIA[d]}
          </div>
        ))}
        {HORAS_SEMANA.map((h) => (
          <div key={h} className="semana-editable__fila" role="row">
            <div className="semana-editable__hora">{h}:00</div>
            {DIAS.map((d) => {
              const tipo = semana.get(clave(d, h));
              return (
                <button
                  key={d}
                  type="button"
                  role="gridcell"
                  className={`celda${tipo ? ` celda--${tipo}` : ""}`}
                  aria-label={`${NOMBRE_DIA[d]} ${h}:00 a ${h + 1}:00${tipo ? `: ${ETIQUETA[tipo]}` : ""}`}
                  onPointerDown={(e) => {
                    e.preventDefault();
                    pintando.current = true;
                    pintar(d, h);
                  }}
                  onPointerEnter={() => pintando.current && pintar(d, h)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && pintar(d, h)}
                />
              );
            })}
          </div>
        ))}
      </div>
      <div className="leyenda">
        {(Object.keys(ETIQUETA) as TipoFranja[]).map((t) => (
          <span key={t}>
            <i className={`celda--${t}`} /> {ETIQUETA[t]}
          </span>
        ))}
      </div>
    </div>
  );
}
