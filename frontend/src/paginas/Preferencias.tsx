import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ErrorApi, api } from "../api/cliente";
import type { Estudiante, Materia, Problema, Profesor, Seccion } from "../api/tipos";
import { Importancia } from "../componentes/preferencias/Importancia";
import { MateriasSolicitadas } from "../componentes/preferencias/MateriasSolicitadas";
import { ProfesoresYCompaneros } from "../componentes/preferencias/ProfesoresYCompaneros";
import { SemanaEditable } from "../componentes/preferencias/SemanaEditable";
import { ErroresDeCampo } from "../componentes/preferencias/ErroresDeCampo";
import { EstadoVacio, Tarjeta } from "../componentes/Tarjeta";
import { useApp } from "../estado/ContextoApp";
import { useRecurso } from "../estado/useRecurso";
import { aplicarSemana, semanaDesde, type Semana } from "../utilidades/franjas";

interface Catalogo {
  estudiantes: Estudiante[];
  materias: Materia[];
  profesores: Profesor[];
  secciones: Seccion[];
  tope: number;
}

function siguienteId(estudiantes: Estudiante[]): string {
  const numeros = estudiantes.map((e) => Number(e.id.replace(/\D/g, ""))).filter(Number.isFinite);
  return `e${String(Math.max(0, ...numeros) + 1).padStart(3, "0")}`;
}

/** Agrupa los errores del servidor por la parte del formulario donde se corrigen. */
function separar(problemas: Problema[]) {
  const de = (...prefijos: string[]) => problemas.filter((p) => prefijos.some((x) => p.campo.startsWith(x)));
  const materias = de("materias");
  const franjas = de("franjas");
  const personas = de("profesores", "social");
  const importancia = de("importancia");
  const ubicados = new Set([...materias, ...franjas, ...personas, ...importancia]);
  return { materias, franjas, personas, importancia, generales: problemas.filter((p) => !ubicados.has(p)) };
}

export function PaginaPreferencias() {
  const { estudianteId } = useParams();
  const esNuevo = estudianteId === "nuevo";
  const catalogo = useRecurso<Catalogo>(async () => {
    const [estudiantes, materias, profesores, secciones, resumen] = await Promise.all([
      api.estudiantes(),
      api.materias(),
      api.profesores(),
      api.secciones(),
      api.resumenDatos(),
    ]);
    return { estudiantes, materias, profesores, secciones, tope: resumen.configuracion.max_creditos ?? 20 };
  }, [estudianteId]);

  if (catalogo.cargando && !catalogo.datos) return <main className="pagina" />;
  if (!catalogo.datos) return <main className="pagina">{catalogo.error && <p className="mensaje mensaje--error">{catalogo.error}</p>}</main>;

  const original = esNuevo
    ? { id: siguienteId(catalogo.datos.estudiantes), nombre: "", semestre: 1, materias: [] }
    : catalogo.datos.estudiantes.find((e) => e.id === estudianteId);

  if (!original) {
    return (
      <main className="pagina">
        <EstadoVacio titulo={`No existe el estudiante ${estudianteId}`}>
          <div className="grupo-botones">
            <Link className="boton" to="/estudiantes">
              ← Volver a Estudiantes
            </Link>
          </div>
        </EstadoVacio>
      </main>
    );
  }
  return <Formulario key={original.id} original={original} catalogo={catalogo.datos} esNuevo={esNuevo} />;
}

function Formulario({ original, catalogo, esNuevo }: { original: Estudiante; catalogo: Catalogo; esNuevo: boolean }) {
  const navegar = useNavigate();
  const { refrescarDatos, seleccionarEstudiante } = useApp();
  const [borrador, setBorrador] = useState<Estudiante>(original);
  const [semana, setSemana] = useState<Semana>(() => semanaDesde(original));
  const [problemas, setProblemas] = useState<Problema[]>([]);
  const [estado, setEstado] = useState<"limpio" | "sucio" | "guardando" | "guardado">(esNuevo ? "sucio" : "limpio");

  useEffect(() => {
    if (!esNuevo) seleccionarEstudiante(original.id);
  }, [esNuevo, original.id, seleccionarEstudiante]);

  // Profesores que dictan las materias pedidas o sus sustitutas: se sugieren primero
  const sugeridos = useMemo(() => {
    const pedidas = new Set(borrador.materias.flatMap((s) => [s.codigo, ...(s.sustitutas ?? [])]));
    return new Set(catalogo.secciones.filter((s) => pedidas.has(s.materia)).map((s) => s.profesor));
  }, [borrador.materias, catalogo.secciones]);

  const cambiar = (cambios: Partial<Estudiante>) => {
    setBorrador((b) => ({ ...b, ...cambios }));
    setEstado("sucio");
  };

  const guardar = async () => {
    setEstado("guardando");
    setProblemas([]);
    const limpio = limpiarVacios(aplicarSemana(borrador, semana));
    try {
      const r = await api.guardarEstudiante(limpio);
      setProblemas(r.advertencias);
      setEstado("guardado");
      refrescarDatos();
      if (esNuevo) navegar(`/estudiantes/${limpio.id}/preferencias`, { replace: true });
    } catch (e) {
      const detalle = e instanceof ErrorApi ? (e.detalle as { problemas?: Problema[] } | undefined) : undefined;
      setProblemas(detalle?.problemas?.length ? detalle.problemas : [{ archivo: "", registro: "", campo: "", mensaje: (e as Error).message, gravedad: "error" }]);
      setEstado("sucio");
    }
  };

  const cancelar = () => {
    setBorrador(original);
    setSemana(semanaDesde(original));
    setProblemas([]);
    setEstado("limpio");
    navegar("/estudiantes");
  };

  const grupos = separar(problemas);
  const hayErrores = problemas.some((p) => p.gravedad === "error");

  return (
    <main className="pagina">
      <div className="pagina__encabezado">
        <div>
          <h1>{esNuevo ? "Nuevo estudiante" : `Preferencias de ${original.nombre}`}</h1>
          <p className="pagina__subtitulo">
            Código <span className="mono">{borrador.id}</span> · Guardar valida los datos antes de escribir <code>estudiantes.json</code>.
          </p>
        </div>
        <div className="grupo-botones">
          {estado === "guardado" && <span className="estado estado--ok">Guardado</span>}
          {hayErrores && <span className="estado estado--error">No se guardó</span>}
          <button className="boton" onClick={cancelar} disabled={estado === "guardando"}>
            Cancelar
          </button>
          <button className="boton boton--primario" onClick={guardar} disabled={estado !== "sucio" || !borrador.nombre.trim()}>
            {estado === "guardando" ? "Guardando…" : "Guardar preferencias"}
          </button>
        </div>
      </div>

      {grupos.generales.length > 0 && (
        <div className="mensaje mensaje--error" style={{ marginBottom: 20 }}>
          <ErroresDeCampo errores={grupos.generales} />
        </div>
      )}

      <div className="rejilla rejilla--mitades">
        <div className="pila">
          <Tarjeta titulo="Datos del estudiante">
            <div className="campos">
              <label className="campo">
                <span className="campo__etiqueta">Nombre</span>
                <input className="entrada" value={borrador.nombre} onChange={(e) => cambiar({ nombre: e.target.value })} />
              </label>
              <label className="campo">
                <span className="campo__etiqueta">Semestre</span>
                <input
                  className="entrada"
                  type="number"
                  min={1}
                  max={10}
                  value={borrador.semestre}
                  onChange={(e) => cambiar({ semestre: Number(e.target.value) })}
                />
              </label>
            </div>
          </Tarjeta>
          <Tarjeta titulo="Materias que necesito" paso={1}>
            <MateriasSolicitadas
              solicitudes={borrador.materias}
              materias={catalogo.materias}
              tope={catalogo.tope}
              errores={grupos.materias}
              alCambiar={(materias) => cambiar({ materias })}
            />
          </Tarjeta>
          <Tarjeta titulo="Profesores y compañeros" paso={3}>
            <ProfesoresYCompaneros
              estudiante={borrador}
              profesores={catalogo.profesores}
              sugeridos={sugeridos}
              companeros={catalogo.estudiantes}
              errores={grupos.personas}
              alCambiar={cambiar}
            />
          </Tarjeta>
        </div>
        <div className="pila">
          <Tarjeta titulo="Mi semana" paso={2} descripcion="Elija qué marcar y haga clic o arrastre sobre las horas.">
            <SemanaEditable
              semana={semana}
              alCambiar={(s) => {
                setSemana(s);
                setEstado("sucio");
              }}
            />
            <ErroresDeCampo errores={grupos.franjas} />
          </Tarjeta>
          <Tarjeta titulo="¿Qué tanto me importa?" paso={4}>
            <Importancia importancia={borrador.importancia} alCambiar={(importancia) => cambiar({ importancia })} />
            <ErroresDeCampo errores={grupos.importancia} />
          </Tarjeta>
        </div>
      </div>
    </main>
  );
}

/** Omite listas y objetos vacíos para que el JSON quede como los demás registros. */
function limpiarVacios(e: Estudiante): Estudiante {
  const copia: Record<string, unknown> = { ...e, materias: e.materias.map((s) => (s.sustitutas?.length ? s : { codigo: s.codigo, prioridad: s.prioridad })) };
  for (const campo of ["profesores", "social"] as const) if (!e[campo]?.length) delete copia[campo];
  if (e.importancia && Object.keys(e.importancia).length === 0) delete copia.importancia;
  return copia as unknown as Estudiante;
}
