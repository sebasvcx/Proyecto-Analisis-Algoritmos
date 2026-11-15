import { useEffect, useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/cliente";
import type { Dia, Estudiante, Materia, Profesor, ResultadoEstudiante, Seccion } from "../api/tipos";
import { GrillaSemanal, type BloqueHorario } from "../componentes/GrillaSemanal";
import { EstadoVacio, Tarjeta } from "../componentes/Tarjeta";
import { useApp } from "../estado/ContextoApp";
import { useCorridaActual } from "../estado/useCorrida";
import { useRecurso } from "../estado/useRecurso";
import { DIAS, fechaCorta } from "../utilidades/formato";

interface EntradaCorrida {
  secciones: Map<string, Seccion>;
  materias: Map<string, Materia>;
  profesores: Map<string, Profesor>;
  estudiantes: Map<string, Estudiante>;
}

const indexar = <T,>(lista: T[], clave: (x: T) => string) => new Map(lista.map((x): [string, T] => [clave(x), x]));

/** Datos con los que se ejecutó la corrida (no los actuales de data/). */
function useEntradaCorrida(id: string | undefined) {
  return useRecurso<EntradaCorrida | null>(async () => {
    if (!id) return null;
    const [secciones, materias, profesores, estudiantes] = await Promise.all([
      api.entradaCorrida<Seccion[]>(id, "secciones"),
      api.entradaCorrida<Materia[]>(id, "materias"),
      api.entradaCorrida<Profesor[]>(id, "profesores"),
      api.entradaCorrida<Estudiante[]>(id, "estudiantes"),
    ]);
    return {
      secciones: indexar(secciones, (s) => s.id),
      materias: indexar(materias, (m) => m.codigo),
      profesores: indexar(profesores, (p) => p.id),
      estudiantes: indexar(estudiantes, (e) => e.id),
    };
  }, [id]);
}

export function PaginaHorario() {
  const { estudianteId } = useParams();
  const navegar = useNavigate();
  const { seleccionarEstudiante } = useApp();
  const corrida = useCorridaActual();
  const salida = corrida.datos;
  const entrada = useEntradaCorrida(salida?.corrida.id);

  // El selector de la barra y la URL se mantienen sincronizados
  useEffect(() => {
    if (estudianteId) seleccionarEstudiante(estudianteId);
  }, [estudianteId, seleccionarEstudiante]);

  const posicion = salida?.estudiantes.findIndex((e) => e.id === estudianteId) ?? -1;
  const resultado = posicion >= 0 ? salida!.estudiantes[posicion] : null;

  if (!salida || !entrada.datos) {
    if (corrida.cargando || entrada.cargando) return <main className="pagina" />;
    return (
      <main className="pagina">
        <EstadoVacio titulo="No hay una corrida para mostrar">
          <div className="grupo-botones">
            <Link className="boton boton--primario" to="/ejecutar">
              Ir a Ejecutar
            </Link>
          </div>
        </EstadoVacio>
      </main>
    );
  }

  if (!resultado) {
    return (
      <main className="pagina">
        <EstadoVacio titulo={`El estudiante ${estudianteId} no participó en esta corrida`}>
          <div className="grupo-botones">
            <Link className="boton" to="/resultados">
              ← Volver a Resultados
            </Link>
          </div>
        </EstadoVacio>
      </main>
    );
  }

  const estudiante = entrada.datos.estudiantes.get(resultado.id);
  const ir = (delta: number) => navegar(`/resultados/${salida.estudiantes[posicion + delta].id}`);

  return (
    <main className="pagina">
      <div className="pagina__encabezado">
        <div>
          <h1>Horario de {estudiante?.nombre ?? resultado.id}</h1>
          <p className="pagina__subtitulo">
            Nivel {salida.corrida.nivel} · corrida del {fechaCorta(salida.corrida.fecha)} · {resultado.creditos} /{" "}
            {salida.corrida.configuracion.max_creditos ?? 20} créditos
          </p>
        </div>
        <div className="grupo-botones">
          <button className="boton" disabled={posicion <= 0} onClick={() => ir(-1)}>
            ‹ Anterior
          </button>
          <button className="boton" disabled={posicion >= salida.estudiantes.length - 1} onClick={() => ir(1)}>
            Siguiente ›
          </button>
          <Link className="boton" to="/resultados">
            ← Volver a Resultados
          </Link>
        </div>
      </div>

      <div className="rejilla rejilla--principal" style={{ gridTemplateColumns: "minmax(0, 2fr) minmax(300px, 1fr)" }}>
        <Semana resultado={resultado} estudiante={estudiante} entrada={entrada.datos} />
        <div className="pila">
          <Avisos resultado={resultado} materias={entrada.datos.materias} />
          <Solicitudes resultado={resultado} materias={entrada.datos.materias} />
        </div>
      </div>
    </main>
  );
}

function Semana({ resultado, estudiante, entrada }: { resultado: ResultadoEstudiante; estudiante?: Estudiante; entrada: EntradaCorrida }) {
  const bloques = useMemo(() => {
    const lista: BloqueHorario[] = [];
    for (const f of estudiante?.franjas_libres ?? []) {
      if ((f.tipo ?? "obligatoria") !== "obligatoria") continue;
      const dias: Dia[] = f.dia === "*" ? DIAS : [f.dia];
      for (const dia of dias) {
        lista.push({ clave: `libre-${dia}-${f.inicio}`, dia, inicio: f.inicio, fin: f.fin, titulo: "No disponible", tipo: "libre" });
      }
    }
    for (const s of resultado.solicitudes) {
      const seccion = s.seccion ? entrada.secciones.get(s.seccion) : undefined;
      if (!seccion) continue;
      const materia = entrada.materias.get(seccion.materia);
      const profesor = entrada.profesores.get(seccion.profesor);
      const sustituta = s.estado === "sustituida";
      seccion.sesiones.forEach((ses, i) =>
        lista.push({
          clave: `${seccion.id}-${i}`,
          dia: ses.dia,
          inicio: ses.inicio,
          fin: ses.fin,
          titulo: `${seccion.id}${sustituta ? " (sustituta)" : ""}`,
          subtitulo: materia?.nombre,
          detalle: `${ses.salon} · ${profesor?.nombre ?? seccion.profesor}`,
          tipo: sustituta ? "sustituta" : "principal",
        }),
      );
    }
    return lista;
  }, [resultado, estudiante, entrada]);

  return <GrillaSemanal bloques={bloques} />;
}

function Avisos({ resultado, materias }: { resultado: ResultadoEstudiante; materias: Map<string, Materia> }) {
  return (
    <Tarjeta titulo="Avisos" paso={1}>
      {resultado.avisos.length === 0 ? (
        <p className="estado estado--ok">Todas las materias pedidas quedaron inscritas.</p>
      ) : (
        resultado.avisos.map((a) => (
          <div key={a.materia} className={`aviso${a.sustituta ? " aviso--sustituida" : ""}`}>
            <div>
              <strong>
                {a.materia} · {materias.get(a.materia)?.nombre}
              </strong>
              {a.sustituta ? <> → inscrita la sustituta {a.sustituta}</> : " — no inscrita"}
            </div>
            <div className="aviso__causa">
              Causa: {a.causa.toLowerCase()}.{a.sugerencia && ` Sugerencia: ${a.sugerencia.toLowerCase()}.`}
            </div>
            {a.causas.length > 1 && <div className="nivel__marca">También: {a.causas.filter((c) => c !== a.causa).join(", ")}</div>}
          </div>
        ))
      )}
    </Tarjeta>
  );
}

const TEXTO_ESTADO = { principal: "Inscrita", sustituida: "Sustituida", no_inscrita: "Pendiente" } as const;
const CLASE_ESTADO = { principal: "estado--ok", sustituida: "estado--aviso", no_inscrita: "estado--error" } as const;

function Solicitudes({ resultado, materias }: { resultado: ResultadoEstudiante; materias: Map<string, Materia> }) {
  return (
    <Tarjeta titulo="Materias solicitadas" paso={2}>
      {resultado.solicitudes.length === 0 ? (
        <p className="pagina__subtitulo">El estudiante no pidió materias.</p>
      ) : (
        <table className="tabla" style={{ background: "transparent" }}>
          <thead>
            <tr>
              <th>Materia</th>
              <th className="numero">Prioridad</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {resultado.solicitudes.map((s) => (
              <tr key={s.materia}>
                <td>
                  <span className="mono">{s.materia}</span>
                  <div className="nivel__marca">
                    {materias.get(s.materia)?.nombre} · {materias.get(s.materia)?.creditos} cr.
                  </div>
                </td>
                <td className="numero">{s.prioridad}</td>
                <td>
                  <span className={`estado ${CLASE_ESTADO[s.estado]}`}>{TEXTO_ESTADO[s.estado]}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Tarjeta>
  );
}
