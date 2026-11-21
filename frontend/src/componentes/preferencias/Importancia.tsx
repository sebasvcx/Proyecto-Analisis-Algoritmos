import type { CriterioSatisfaccion, Estudiante } from "../../api/tipos";
import { Segmentado } from "../Tarjeta";

type Nivel = "ninguna" | "baja" | "media" | "alta";

export const CRITERIOS: { clave: CriterioSatisfaccion; texto: string; ayuda: string }[] = [
  { clave: "horario", texto: "Horario", ayuda: "franjas preferidas, a evitar y libres deseables" },
  { clave: "profesores", texto: "Profesores", ayuda: "afinidad con quien dicta" },
  { clave: "cercania", texto: "Cercanía", ayuda: "poca caminata entre clases seguidas" },
  { clave: "huecos", texto: "Huecos", ayuda: "pocas horas muertas entre clases" },
  { clave: "social", texto: "Compañeros", ayuda: "quedar con amigos, lejos de quien evita" },
];

const NIVELES: { valor: Nivel; texto: string }[] = [
  { valor: "ninguna", texto: "Nada" },
  { valor: "baja", texto: "Baja" },
  { valor: "media", texto: "Media" },
  { valor: "alta", texto: "Alta" },
];

// Sección 5.5: sin peso declarado se usa media (2), excepto huecos, que usa baja (1)
const POR_DEFECTO: Record<CriterioSatisfaccion, Nivel> = { horario: "media", profesores: "media", cercania: "media", huecos: "baja", social: "media" };

export function Importancia({ importancia, alCambiar }: { importancia: Estudiante["importancia"]; alCambiar: (i: Estudiante["importancia"]) => void }) {
  const actual = importancia ?? {};
  return (
    <div className="lista-importancia">
      {CRITERIOS.map((c) => (
        <div key={c.clave} className="lista-importancia__fila">
          <div>
            <div>{c.texto}</div>
            <div className="nivel__marca">{c.ayuda}</div>
          </div>
          <Segmentado
            etiqueta={`Importancia de ${c.texto}`}
            opciones={NIVELES}
            valor={actual[c.clave] ?? POR_DEFECTO[c.clave]}
            alCambiar={(v) => alCambiar({ ...actual, [c.clave]: v })}
          />
        </div>
      ))}
      <p className="nivel__marca" style={{ marginTop: 6 }}>
        La importancia se usa desde el nivel 8. Nunca hace perder una materia: solo decide entre secciones válidas.
      </p>
    </div>
  );
}
