import type { ReactNode } from "react";

interface Props {
  titulo?: string;
  paso?: number;
  descripcion?: string;
  acciones?: ReactNode;
  blanca?: boolean;
  children: ReactNode;
}

/** Contenedor con título y número de paso, como en los mockups. */
export function Tarjeta({ titulo, paso, descripcion, acciones, blanca, children }: Props) {
  return (
    <section className={`tarjeta${blanca ? " tarjeta--blanca" : ""}`}>
      {titulo && (
        <header className="tarjeta__titulo">
          {paso !== undefined && <span className="paso">{paso}</span>}
          <h2 style={{ flex: 1 }}>{titulo}</h2>
          {acciones}
        </header>
      )}
      {descripcion && <p className="tarjeta__descripcion">{descripcion}</p>}
      {children}
    </section>
  );
}

export function Segmentado<T extends string | boolean>({
  opciones,
  valor,
  alCambiar,
  etiqueta,
}: {
  opciones: { valor: T; texto: string }[];
  valor: T;
  alCambiar: (v: T) => void;
  etiqueta: string;
}) {
  return (
    <div className="segmentado" role="group" aria-label={etiqueta}>
      {opciones.map((o) => (
        <button key={String(o.valor)} type="button" aria-pressed={o.valor === valor} onClick={() => alCambiar(o.valor)}>
          {o.texto}
        </button>
      ))}
    </div>
  );
}

export function EstadoVacio({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className="vacio">
      <h2>{titulo}</h2>
      {children}
    </div>
  );
}
