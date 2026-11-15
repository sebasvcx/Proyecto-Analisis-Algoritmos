import { useMemo } from "react";
import { Link } from "react-router-dom";
import type { ResultadoEstudiante, Salida } from "../api/tipos";
import { EstadoVacio, Tarjeta } from "../componentes/Tarjeta";
import { useApp } from "../estado/ContextoApp";
import { useCorridaActual } from "../estado/useCorrida";
import { fechaCorta, numero, porcentaje } from "../utilidades/formato";

export function PaginaResultados() {
  const corrida = useCorridaActual();
  const { seleccionarCorrida } = useApp();
  const salida = corrida.datos;

  if (corrida.cargando && !salida) return <main className="pagina" />;
  if (!salida) {
    return (
      <main className="pagina">
        <EstadoVacio titulo="Todavía no hay resultados">
          <p>Ejecute una corrida para ver la asignación.</p>
          <div className="grupo-botones">
            <Link className="boton boton--primario" to="/ejecutar">
              Ir a Ejecutar
            </Link>
          </div>
        </EstadoVacio>
      </main>
    );
  }

  const { corrida: c, resumen } = salida;
  return (
    <main className="pagina">
      <div className="pagina__encabezado">
        <div>
          <h1>Resultados de la corrida</h1>
          <p className="pagina__subtitulo">
            Nivel {c.nivel} ({c.nombre_nivel}) · {c.estudiantes} estudiantes · {c.secciones} secciones · {fechaCorta(c.fecha)}
          </p>
        </div>
        <div className="grupo-botones">
          <select className="entrada" style={{ width: "auto" }} value={c.id} onChange={(e) => seleccionarCorrida(e.target.value)}>
            {corrida.corridas.map((x) => (
              <option key={x.id} value={x.id}>
                N{x.nivel} · {fechaCorta(x.fecha)}
              </option>
            ))}
          </select>
          <button className="boton" onClick={() => descargar(salida)}>
            Descargar salida.json
          </button>
        </div>
      </div>

      <div className="indicadores">
        <Indicador valor={porcentaje(resumen.cobertura)} etiqueta="Solicitudes atendidas" />
        <Indicador valor={porcentaje(resumen.indicador_academico)} etiqueta="Indicador académico (ponderado por prioridad)" />
        <Indicador valor={String(resumen.solicitudes.pendientes)} etiqueta={`Pendientes de ${resumen.solicitudes.total}`} />
        <Indicador
          valor={String(salida.verificacion.total)}
          etiqueta="Reglas violadas (verificador)"
          tono={salida.verificacion.total ? "mal" : "bien"}
        />
        <Indicador valor={`${numero(c.tiempo_algoritmo_s * 1000)} ms`} etiqueta="Tiempo del algoritmo" />
      </div>

      <div className="rejilla rejilla--principal">
        <PeorAtendidos salida={salida} />
        <div className="pila">
          <Tarjeta titulo="Atención por prioridad" paso={1} descripcion="Se compara primero la prioridad 5; solo si empata se pasa a la 4, y así hasta 1.">
            <div className="barras">
              {resumen.por_prioridad.map((p) => (
                <div key={p.prioridad} className="barra-dato">
                  <span>Prioridad {p.prioridad}</span>
                  <div className="barra-dato__pista">
                    <div className="barra-dato__relleno" style={{ width: p.pedidas ? `${(p.puntaje / p.pedidas) * 100}%` : 0 }} />
                  </div>
                  <span className="barra-dato__valor">
                    {numero(p.puntaje)} / {p.pedidas}
                  </span>
                </div>
              ))}
            </div>
          </Tarjeta>
          <Verificacion salida={salida} />
        </div>
      </div>
    </main>
  );
}

function Indicador({ valor, etiqueta, tono }: { valor: string; etiqueta: string; tono?: "bien" | "mal" }) {
  return (
    <div className="indicador">
      <div className={`indicador__valor${tono ? ` indicador__valor--${tono}` : ""}`}>{valor}</div>
      <div className="indicador__etiqueta">{etiqueta}</div>
    </div>
  );
}

function Verificacion({ salida }: { salida: Salida }) {
  const cubiertas = new Set(salida.corrida.reglas_del_nivel);
  return (
    <Tarjeta titulo="Verificación de reglas" paso={2} descripcion="Un verificador separado recalcula las reglas sobre la salida guardada.">
      <div className="barras">
        {Object.entries(salida.verificacion.por_regla).map(([regla, total]) => (
          <div key={regla} className="barra-dato" style={{ gridTemplateColumns: "48px 1fr auto" }}>
            <strong>{regla}</strong>
            <span className={`estado ${total ? (cubiertas.has(regla) ? "estado--error" : "estado--aviso") : "estado--ok"}`}>
              {total ? `${total} ${total === 1 ? "violación" : "violaciones"}` : "cumple"}
            </span>
            {!cubiertas.has(regla) && regla !== "E" && <span className="nivel__marca">no aplica en N{salida.corrida.nivel}</span>}
          </div>
        ))}
      </div>
      {salida.verificacion.total > 0 && salida.corrida.reglas_del_nivel.length < salida.verificacion.reglas_verificadas.length && (
        <p className="mensaje mensaje--aviso" style={{ marginTop: 14 }}>
          Este nivel es de prueba: todavía no aplica todas las reglas, por eso el verificador las reporta.
        </p>
      )}
    </Tarjeta>
  );
}

function deficit(e: ResultadoEstudiante): number {
  return e.solicitudes.filter((s) => s.estado === "no_inscrita").reduce((suma, s) => suma + s.prioridad, 0);
}

function PeorAtendidos({ salida }: { salida: Salida }) {
  const { seleccionarEstudiante, estudiantes } = useApp();
  const nombres = useMemo(() => new Map(estudiantes.map((e): [string, string] => [e.id, e.nombre])), [estudiantes]);
  const ordenados = useMemo(
    () =>
      [...salida.estudiantes]
        .filter((e) => e.solicitudes.length > 0)
        .sort((a, b) => deficit(b) - deficit(a) || a.id.localeCompare(b.id))
        .slice(0, 12),
    [salida],
  );

  return (
    <Tarjeta titulo="Estudiantes peor atendidos" paso={3} descripcion="Ordenados por la suma de prioridades de sus materias pendientes." blanca>
      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Estudiante</th>
              <th className="numero">Inscritas</th>
              <th className="numero">Créditos</th>
              <th className="numero">Avisos</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {ordenados.map((e) => {
              const inscritas = e.solicitudes.filter((s) => s.estado !== "no_inscrita").length;
              return (
                <tr key={e.id}>
                  <td>
                    <span className="mono">{e.id}</span> · {nombres.get(e.id) ?? ""}
                  </td>
                  <td className="numero">
                    {inscritas} / {e.solicitudes.length}
                  </td>
                  <td className="numero">{e.creditos}</td>
                  <td className="numero" style={{ color: e.avisos.length ? "var(--rojo-700)" : undefined }}>
                    {e.avisos.length}
                  </td>
                  <td>
                    <Link className="boton boton--chico" to={`/resultados/${e.id}`} onClick={() => seleccionarEstudiante(e.id)}>
                      Ver horario →
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Tarjeta>
  );
}

function descargar(salida: Salida) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(salida, null, 2)], { type: "application/json" }));
  const enlace = Object.assign(document.createElement("a"), { href: url, download: `salida-${salida.corrida.id}.json` });
  enlace.click();
  URL.revokeObjectURL(url);
}
