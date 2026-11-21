import type { Materia, Problema, SolicitudJson } from "../../api/tipos";
import { Segmentado } from "../Tarjeta";
import { ErroresDeCampo } from "./ErroresDeCampo";

interface Props {
  solicitudes: SolicitudJson[];
  materias: Materia[];
  tope: number;
  errores: Problema[];
  alCambiar: (solicitudes: SolicitudJson[]) => void;
}

const PRIORIDADES = [1, 2, 3, 4, 5].map((p) => ({ valor: String(p), texto: String(p) }));

/** Materias que necesita, su prioridad (1 = puedo vivir sin ella, 5 = la necesito) y sustitutas en orden. */
export function MateriasSolicitadas({ solicitudes, materias, tope, errores, alCambiar }: Props) {
  const porCodigo = new Map(materias.map((m): [string, Materia] => [m.codigo, m]));
  const principales = new Set(solicitudes.map((s) => s.codigo));
  const creditos = solicitudes.reduce((suma, s) => suma + (porCodigo.get(s.codigo)?.creditos ?? 0), 0);
  const disponibles = materias.filter((m) => !principales.has(m.codigo));

  const actualizar = (i: number, cambios: Partial<SolicitudJson>) =>
    alCambiar(solicitudes.map((s, j) => (j === i ? { ...s, ...cambios } : s)));

  const agregar = () => {
    const primera = disponibles[0];
    if (primera) alCambiar([...solicitudes, { codigo: primera.codigo, prioridad: 3 }]);
  };

  return (
    <div>
      {solicitudes.length === 0 ? (
        <p className="pagina__subtitulo">Todavía no pide ninguna materia.</p>
      ) : (
        <ul className="solicitudes">
          {solicitudes.map((s, i) => {
            // Una sustituta no puede ser una materia pedida ni repetirse en la lista
            const opcionesSustituta = materias.filter((m) => !principales.has(m.codigo) && !(s.sustitutas ?? []).includes(m.codigo));
            return (
              <li key={`${s.codigo}-${i}`} className="solicitud">
                <div className="solicitud__fila">
                  <select
                    className="entrada"
                    value={s.codigo}
                    aria-label="Materia"
                    onChange={(e) =>
                      actualizar(i, { codigo: e.target.value, sustitutas: (s.sustitutas ?? []).filter((x) => x !== e.target.value) })
                    }
                  >
                    {[porCodigo.get(s.codigo), ...disponibles].filter(Boolean).map((m) => (
                      <option key={m!.codigo} value={m!.codigo}>
                        {m!.codigo} · {m!.nombre} ({m!.creditos} cr.)
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="boton boton--chico boton--icono"
                    aria-label={`Quitar ${s.codigo}`}
                    title="Quitar materia"
                    onClick={() => alCambiar(solicitudes.filter((_, j) => j !== i))}
                  >
                    ×
                  </button>
                </div>
                <div className="solicitud__fila">
                  <span className="campo__etiqueta">Prioridad</span>
                  <Segmentado
                    etiqueta={`Prioridad de ${s.codigo}`}
                    opciones={PRIORIDADES}
                    valor={String(s.prioridad)}
                    alCambiar={(p) => actualizar(i, { prioridad: Number(p) })}
                  />
                  <div className="chips solicitud__sustitutas">
                    {(s.sustitutas ?? []).map((codigo, posicion) => (
                      <button
                        key={codigo}
                        type="button"
                        className="chip chip--quitable"
                        title="Quitar sustituta"
                        onClick={() => actualizar(i, { sustitutas: (s.sustitutas ?? []).filter((x) => x !== codigo) })}
                      >
                        {posicion + 1}. {codigo} ×
                      </button>
                    ))}
                    {opcionesSustituta.length > 0 && (
                      <select
                        className="entrada entrada--compacta"
                        value=""
                        aria-label={`Agregar sustituta a ${s.codigo}`}
                        onChange={(e) => e.target.value && actualizar(i, { sustitutas: [...(s.sustitutas ?? []), e.target.value] })}
                      >
                        <option value="">+ sustituta</option>
                        {opcionesSustituta.map((m) => (
                          <option key={m.codigo} value={m.codigo}>
                            {m.codigo} · {m.nombre}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
      <div className="fila-acciones">
        <button type="button" className="boton boton--chico" onClick={agregar} disabled={disponibles.length === 0}>
          + Agregar materia
        </button>
        <span className={`estado ${creditos > tope ? "estado--aviso" : "estado--neutro"}`}>
          Créditos pedidos: {creditos} / {tope}
          {creditos > tope && " (no todas podrán inscribirse)"}
        </span>
      </div>
      <ErroresDeCampo errores={errores} />
    </div>
  );
}
