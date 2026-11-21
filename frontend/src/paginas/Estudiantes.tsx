import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/cliente";
import type { Materia } from "../api/tipos";
import { EstadoVacio } from "../componentes/Tarjeta";
import { useApp } from "../estado/ContextoApp";
import { useRecurso } from "../estado/useRecurso";
import { trabaja } from "../utilidades/formato";

const POR_PAGINA = 20;

export function PaginaEstudiantes() {
  const { estudiantes, estudianteActivo, seleccionarEstudiante, corridaActiva } = useApp();
  const materias = useRecurso(api.materias);
  const config = useRecurso(() => api.resumenDatos().then((r) => r.configuracion));
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(0);

  const creditos = useMemo(() => new Map((materias.datos ?? []).map((m: Materia): [string, number] => [m.codigo, m.creditos])), [materias.datos]);
  const tope = config.datos?.max_creditos ?? 20;

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!q) return estudiantes;
    return estudiantes.filter((e) => e.id.toLowerCase().includes(q) || e.nombre.toLowerCase().includes(q));
  }, [estudiantes, busqueda]);

  const paginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA));
  const actual = Math.min(pagina, paginas - 1);
  const visibles = filtrados.slice(actual * POR_PAGINA, (actual + 1) * POR_PAGINA);

  if (estudiantes.length === 0) {
    return (
      <main className="pagina">
        <EstadoVacio titulo="Aún no hay estudiantes">
          <p>Importe estudiantes.json o genere una instancia de prueba.</p>
          <div className="grupo-botones">
            <Link className="boton boton--primario" to="/datos">
              Ir a Datos
            </Link>
          </div>
        </EstadoVacio>
      </main>
    );
  }

  return (
    <main className="pagina">
      <div className="pagina__encabezado">
        <div>
          <h1>Estudiantes</h1>
          <p className="pagina__subtitulo">
            {estudiantes.length} estudiantes en <code>estudiantes.json</code>
          </p>
        </div>
        <div className="grupo-botones">
        <input
          className="entrada"
          style={{ maxWidth: 280 }}
          type="search"
          placeholder="Buscar por nombre o código…"
          value={busqueda}
          onChange={(e) => {
            setBusqueda(e.target.value);
            setPagina(0);
          }}
        />
        <Link className="boton boton--primario" to="/estudiantes/nuevo/preferencias">
          + Nuevo estudiante
        </Link>
        </div>
      </div>

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th className="numero">Semestre</th>
              <th>Materias solicitadas (prioridad)</th>
              <th className="numero">Créditos pedidos</th>
              <th>Trabaja</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {visibles.map((e) => {
              const pedidos = e.materias.reduce((suma, s) => suma + (creditos.get(s.codigo) ?? 0), 0);
              return (
                <tr key={e.id} aria-selected={e.id === estudianteActivo?.id}>
                  <td className="mono">{e.id}</td>
                  <td>{e.nombre}</td>
                  <td className="numero">{e.semestre}</td>
                  <td>
                    <div className="chips">
                      {[...e.materias]
                        .sort((a, b) => b.prioridad - a.prioridad)
                        .map((s) => (
                          <span key={s.codigo} className={`chip${s.prioridad === 5 ? " chip--p5" : ""}`} title={sustitutasTexto(s.sustitutas)}>
                            {s.codigo} <span className="chip__prioridad">{s.prioridad}</span>
                          </span>
                        ))}
                    </div>
                  </td>
                  <td className="numero" style={{ color: pedidos > tope ? "var(--rojo-700)" : undefined }}>
                    {pedidos} / {tope}
                  </td>
                  <td>{trabaja(e) ? "Sí" : "No"}</td>
                  <td>
                    <div className="grupo-botones" style={{ justifyContent: "flex-end" }}>
                      <Link className="boton boton--chico boton--primario" to={`/estudiantes/${e.id}/preferencias`}>
                        Editar preferencias
                      </Link>
                      {corridaActiva && (
                        <Link className="boton boton--chico" to={`/resultados/${e.id}`} onClick={() => seleccionarEstudiante(e.id)}>
                          Ver horario
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="paginacion">
        <span>
          Mostrando {filtrados.length ? actual * POR_PAGINA + 1 : 0}–{Math.min((actual + 1) * POR_PAGINA, filtrados.length)} de {filtrados.length}
        </span>
        <div className="grupo-botones">
          <button className="boton boton--chico" disabled={actual === 0} onClick={() => setPagina(actual - 1)}>
            ‹ Anterior
          </button>
          <button className="boton boton--chico" disabled={actual >= paginas - 1} onClick={() => setPagina(actual + 1)}>
            Siguiente ›
          </button>
        </div>
      </div>
    </main>
  );
}

function sustitutasTexto(sustitutas?: string[]): string | undefined {
  return sustitutas?.length ? `Sustitutas: ${sustitutas.join(", ")}` : undefined;
}
