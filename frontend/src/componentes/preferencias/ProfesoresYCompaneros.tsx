import type { Estudiante, Problema, Profesor } from "../../api/tipos";
import { Segmentado } from "../Tarjeta";
import { ErroresDeCampo } from "./ErroresDeCampo";

type Opinion = NonNullable<Estudiante["profesores"]>[number];
type Social = NonNullable<Estudiante["social"]>[number];

const AFINIDADES = ["-2", "-1", "0", "+1", "+2"].map((t) => ({ valor: String(Number(t)), texto: t }));
const COMPANERO = [
  { valor: "2", texto: "Amigo" },
  { valor: "1", texto: "Bien" },
  { valor: "-1", texto: "Mejor no" },
  { valor: "-2", texto: "Evitar" },
];

interface Props {
  estudiante: Estudiante;
  profesores: Profesor[];
  /** Profesores que dictan alguna sección de las materias pedidas (se sugieren primero). */
  sugeridos: Set<string>;
  companeros: Estudiante[];
  errores: Problema[];
  alCambiar: (cambios: Pick<Estudiante, "profesores" | "social">) => void;
}

/**
 * Afinidad con profesores de -2 a +2 y veto aparte (un veto es la regla R7; la
 * afinidad negativa solo es una preferencia). Compañeros: amigos y personas a evitar.
 */
export function ProfesoresYCompaneros({ estudiante, profesores, sugeridos, companeros, errores, alCambiar }: Props) {
  const opiniones = estudiante.profesores ?? [];
  const social = estudiante.social ?? [];
  const nombreProfesor = new Map(profesores.map((p): [string, string] => [p.id, p.nombre]));
  const nombreCompanero = new Map(companeros.map((e): [string, string] => [e.id, e.nombre]));

  const cambiarOpiniones = (lista: Opinion[]) => alCambiar({ profesores: lista, social });
  const cambiarSocial = (lista: Social[]) => alCambiar({ profesores: opiniones, social: lista });

  const sinOpinion = profesores
    .filter((p) => !opiniones.some((o) => o.id === p.id))
    .sort((a, b) => Number(sugeridos.has(b.id)) - Number(sugeridos.has(a.id)) || a.nombre.localeCompare(b.nombre));
  const sinRelacion = companeros.filter((e) => e.id !== estudiante.id && !social.some((s) => s.estudiante === e.id));

  return (
    <div className="pila" style={{ gap: 18 }}>
      <div>
        <h3 className="subtitulo-seccion">Profesores</h3>
        {opiniones.length === 0 && <p className="pagina__subtitulo">Sin opiniones: todos los profesores valen lo mismo.</p>}
        <ul className="lista-opiniones">
          {opiniones.map((o, i) => (
            <li key={o.id}>
              <span className="lista-opiniones__nombre">
                {nombreProfesor.get(o.id) ?? o.id}
                {sugeridos.has(o.id) && <span className="nivel__marca"> · dicta materias pedidas</span>}
              </span>
              {o.veto ? (
                <span className="estado estado--error">Vetado</span>
              ) : (
                <Segmentado
                  etiqueta={`Afinidad con ${o.id}`}
                  opciones={AFINIDADES}
                  valor={String(o.afinidad ?? 0)}
                  alCambiar={(v) => cambiarOpiniones(opiniones.map((x, j) => (j === i ? { id: x.id, afinidad: Number(v) } : x)))}
                />
              )}
              <label className="casilla">
                <input
                  type="checkbox"
                  checked={o.veto === true}
                  onChange={(e) =>
                    cambiarOpiniones(opiniones.map((x, j) => (j === i ? (e.target.checked ? { id: x.id, veto: true } : { id: x.id, afinidad: 0 }) : x)))
                  }
                />
                Veto
              </label>
              <button
                type="button"
                className="boton boton--chico boton--icono"
                aria-label={`Quitar ${o.id}`}
                title="Quitar"
                onClick={() => cambiarOpiniones(opiniones.filter((_, j) => j !== i))}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
        {sinOpinion.length > 0 && (
          <select
            className="entrada entrada--compacta"
            value=""
            aria-label="Agregar profesor"
            onChange={(e) => e.target.value && cambiarOpiniones([...opiniones, { id: e.target.value, afinidad: 1 }])}
          >
            <option value="">+ Opinar sobre un profesor</option>
            {sinOpinion.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
                {sugeridos.has(p.id) ? " (dicta materias pedidas)" : ""}
              </option>
            ))}
          </select>
        )}
      </div>

      <div>
        <h3 className="subtitulo-seccion">Compañeros</h3>
        {social.length === 0 && <p className="pagina__subtitulo">Sin amigos ni personas a evitar.</p>}
        <ul className="lista-opiniones">
          {social.map((s, i) => (
            <li key={s.estudiante}>
              <span className="lista-opiniones__nombre">
                {nombreCompanero.get(s.estudiante) ?? s.estudiante} <span className="mono nivel__marca">{s.estudiante}</span>
              </span>
              <Segmentado
                etiqueta={`Relación con ${s.estudiante}`}
                opciones={COMPANERO}
                valor={String(s.afinidad)}
                alCambiar={(v) => cambiarSocial(social.map((x, j) => (j === i ? { ...x, afinidad: Number(v) } : x)))}
              />
              <button
                type="button"
                className="boton boton--chico boton--icono"
                aria-label={`Quitar ${s.estudiante}`}
                title="Quitar"
                onClick={() => cambiarSocial(social.filter((_, j) => j !== i))}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
        {sinRelacion.length > 0 && (
          <select
            className="entrada entrada--compacta"
            value=""
            aria-label="Agregar compañero"
            onChange={(e) => e.target.value && cambiarSocial([...social, { estudiante: e.target.value, afinidad: 2 }])}
          >
            <option value="">+ Agregar compañero</option>
            {sinRelacion.map((e) => (
              <option key={e.id} value={e.id}>
                {e.id} · {e.nombre}
              </option>
            ))}
          </select>
        )}
      </div>
      <ErroresDeCampo errores={errores} />
    </div>
  );
}
