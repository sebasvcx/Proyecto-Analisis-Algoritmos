import { useState } from "react";
import { api } from "../../api/cliente";
import type { FilaComparacion } from "../../api/tipos";
import { numero, porcentaje } from "../../utilidades/formato";
import { Segmentado, Tarjeta } from "../Tarjeta";

type Metrica = "cobertura" | "indicador_academico" | "satisfaccion_promedio" | "c5";

const METRICAS: { valor: Metrica; texto: string }[] = [
  { valor: "cobertura", texto: "Atendidas" },
  { valor: "c5", texto: "Prioridad 5" },
  { valor: "indicador_academico", texto: "Académico" },
  { valor: "satisfaccion_promedio", texto: "Satisfacción" },
];

const esReferencia = (f: FilaComparacion) => f.metodo === "aleatoria" || f.metodo === "llegada";

/**
 * Ejecuta las dos asignaciones de referencia y todos los niveles sobre los datos
 * actuales (sin guardar) y los compara. N1 y N2 no aplican todas las reglas, así
 * que sus violaciones se marcan.
 */
export function ComparacionNiveles({ actual }: { actual: string }) {
  const [filas, setFilas] = useState<FilaComparacion[] | null>(null);
  const [metrica, setMetrica] = useState<Metrica>("cobertura");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const comparar = async () => {
    setCargando(true);
    setError(null);
    try {
      setFilas(await api.comparacion());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
    }
  };

  const valor = (f: FilaComparacion) => (f[metrica] ?? 0) as number;
  const maximo = filas ? Math.max(...filas.map(valor), 1e-9) : 1;
  const formato = (f: FilaComparacion) => (metrica === "c5" ? numero(valor(f)) : porcentaje(valor(f)));

  return (
    <Tarjeta
      titulo="Comparación entre niveles"
      paso={5}
      descripcion="Mismos datos actuales de data/, sin guardar. En gris, las asignaciones de comparación; en naranja, la corrida que está viendo."
      acciones={
        <button className="boton boton--chico" onClick={comparar} disabled={cargando}>
          {cargando ? "Comparando…" : filas ? "Volver a comparar" : "Comparar todos"}
        </button>
      }
      blanca
    >
      {error && <p className="mensaje mensaje--error">{error}</p>}
      {!filas && !error && (
        <p className="pagina__subtitulo">Ejecuta la aleatoria, la de llegada y N1 a N10 sobre los mismos datos (unos segundos).</p>
      )}
      {filas && (
        <>
          <Segmentado etiqueta="Métrica" opciones={METRICAS} valor={metrica} alCambiar={setMetrica} />
          <div className="columnas" role="img" aria-label={`Gráfica de ${metrica} por método; los valores están en la tabla`}>
            {filas.map((f) => (
              <div key={f.metodo} className="columna">
                <span className="columna__valor">{formato(f)}</span>
                <div
                  className={`columna__barra${esReferencia(f) ? " columna__barra--referencia" : ""}${f.metodo === actual ? " columna__barra--elegida" : ""}`}
                  style={{ height: `${(valor(f) / maximo) * 82}%` }}
                />
              </div>
            ))}
          </div>
          <div className="columnas__etiquetas" aria-hidden>
            {filas.map((f) => (
              <span key={f.metodo}>{f.etiqueta}</span>
            ))}
          </div>
          <div className="tabla-contenedor" style={{ marginTop: 16 }}>
            <table className="tabla">
              <thead>
                <tr>
                  <th>Método</th>
                  <th className="numero">Atendidas</th>
                  <th className="numero">C5 · C4 · C3 · C2 · C1</th>
                  <th className="numero">Satisf.</th>
                  <th className="numero">Mín.</th>
                  <th className="numero">Reglas</th>
                  <th className="numero">Tiempo</th>
                </tr>
              </thead>
              <tbody>
                {filas.map((f) => (
                  <tr key={f.metodo} aria-selected={f.metodo === actual}>
                    <td>{f.etiqueta}</td>
                    <td className="numero">{porcentaje(f.cobertura, 1)}</td>
                    <td className="numero mono">{[f.c5, f.c4, f.c3, f.c2, f.c1].map(numero).join(" · ")}</td>
                    <td className="numero">{porcentaje(f.satisfaccion_promedio)}</td>
                    <td className="numero">{porcentaje(f.satisfaccion_minima)}</td>
                    <td className="numero" style={{ color: f.violaciones ? "var(--ambar-700)" : undefined }}>
                      {f.violaciones ? `${f.violaciones} viol.` : "ok"}
                    </td>
                    <td className="numero">{numero(f.tiempo_algoritmo_s * 1000)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="nivel__marca" style={{ marginTop: 8 }}>
            N1 y N2 todavía no aplican todas las reglas, por eso pueden tener violaciones. Las demás comparan en igualdad de condiciones.
          </p>
        </>
      )}
    </Tarjeta>
  );
}
