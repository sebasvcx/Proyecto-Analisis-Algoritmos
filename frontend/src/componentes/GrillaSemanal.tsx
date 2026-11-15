import type { Dia } from "../api/tipos";
import { DIAS, HORA_APERTURA, HORA_CIERRE, NOMBRE_DIA, aMinutos } from "../utilidades/formato";

export interface BloqueHorario {
  clave: string;
  dia: Dia;
  inicio: string;
  fin: string;
  titulo: string;
  subtitulo?: string;
  detalle?: string;
  tipo: "principal" | "sustituta" | "libre";
}

const HORAS = Array.from({ length: (HORA_CIERRE - HORA_APERTURA) / 60 }, (_, i) => HORA_APERTURA / 60 + i);

/** Semana de lunes a sábado, 07:00–20:00. La posición de cada bloque se calcula en horas. */
export function GrillaSemanal({ bloques }: { bloques: BloqueHorario[] }) {
  return (
    <div>
      <div className="grilla" role="table" aria-label="Horario semanal">
        <div className="grilla__esquina" />
        {DIAS.map((d) => (
          <div key={d} className="grilla__dia-titulo" role="columnheader">
            {NOMBRE_DIA[d]}
          </div>
        ))}

        <div className="grilla__horas" aria-hidden>
          {HORAS.map((h) => (
            <div key={h} className="grilla__hora">
              {h}:00
            </div>
          ))}
        </div>

        {DIAS.map((dia) => (
          <div key={dia} className="grilla__columna" role="cell">
            {bloques
              .filter((b) => b.dia === dia)
              .map((b) => {
                const inicio = (aMinutos(b.inicio) - HORA_APERTURA) / 60;
                const duracion = (aMinutos(b.fin) - aMinutos(b.inicio)) / 60;
                return (
                  <div
                    key={b.clave}
                    className={`bloque bloque--${b.tipo}`}
                    style={{
                      top: `calc(${inicio} * var(--alto-hora) + 2px)`,
                      height: `calc(${duracion} * var(--alto-hora) - 4px)`,
                    }}
                    title={`${b.titulo} · ${b.inicio}–${b.fin}`}
                  >
                    <strong>{b.titulo}</strong>
                    {b.subtitulo && <div>{b.subtitulo}</div>}
                    {b.detalle && <div className="bloque__detalle">{b.detalle}</div>}
                  </div>
                );
              })}
          </div>
        ))}
      </div>
      <div className="leyenda">
        <span>
          <i /> Materia principal
        </span>
        <span>
          <i className="sustituta" /> Sustituta
        </span>
        <span>
          <i className="libre" /> Franja obligatoriamente libre
        </span>
      </div>
    </div>
  );
}
