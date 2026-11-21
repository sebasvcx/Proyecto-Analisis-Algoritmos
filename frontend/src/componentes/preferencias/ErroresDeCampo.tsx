import type { Problema } from "../../api/tipos";

/** Errores que devolvió el servidor para una parte del formulario. */
export function ErroresDeCampo({ errores }: { errores: Problema[] }) {
  if (errores.length === 0) return null;
  return (
    <ul className="problemas" style={{ marginTop: 12 }}>
      {errores.map((p, i) => (
        <li key={i}>
          <span className={`estado ${p.gravedad === "error" ? "estado--error" : "estado--aviso"}`} />
          <span>
            {p.campo && <span className="problemas__ruta">{p.campo}</span>}
            {p.campo && " — "}
            {p.mensaje}
          </span>
        </li>
      ))}
    </ul>
  );
}
