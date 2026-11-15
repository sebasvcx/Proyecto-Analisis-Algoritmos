import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/cliente";
import type { Entidad, Escasez, ParametrosGeneracion, ResumenDatos } from "../api/tipos";
import { Segmentado, Tarjeta } from "../componentes/Tarjeta";
import { useApp } from "../estado/ContextoApp";
import { useRecurso } from "../estado/useRecurso";

const NOMBRE_REGISTRO: Record<Entidad, string> = {
  materias: "materias",
  profesores: "profesores",
  edificios: "edificios",
  traslados: "traslados",
  secciones: "secciones",
  estudiantes: "estudiantes",
  config: "",
};

export function PaginaDatos() {
  const resumen = useRecurso(api.resumenDatos);
  const { refrescarDatos } = useApp();
  const [mensaje, setMensaje] = useState<string | null>(null);

  const actualizar = (texto: string) => {
    setMensaje(texto);
    resumen.recargar();
    refrescarDatos();
  };

  return (
    <main className="pagina">
      <div className="pagina__encabezado">
        <div>
          <h1>Datos de la instancia</h1>
          <p className="pagina__subtitulo">
            Los archivos JSON de la carpeta <code>data/</code> son la fuente de toda la información.
          </p>
        </div>
      </div>

      {mensaje && (
        <p className="mensaje mensaje--info" style={{ marginBottom: 20 }}>
          {mensaje}
        </p>
      )}

      <div className="rejilla rejilla--principal">
        <div className="pila">
          <Archivos resumen={resumen.datos} error={resumen.error} alImportar={actualizar} />
          {resumen.datos && <Validacion resumen={resumen.datos} />}
        </div>
        <div className="pila">
          <Generar alGenerar={actualizar} />
          <Tarjeta titulo="Siguiente paso">
            <div className="grupo-botones">
              <Link className="boton" to="/estudiantes">
                Ir a Estudiantes →
              </Link>
              <Link className="boton boton--primario" to="/ejecutar">
                Ir a Ejecutar →
              </Link>
            </div>
          </Tarjeta>
        </div>
      </div>
    </main>
  );
}

function Archivos({
  resumen,
  error,
  alImportar,
}: {
  resumen: ResumenDatos | null;
  error: string | null;
  alImportar: (mensaje: string) => void;
}) {
  const entradaArchivos = useRef<HTMLInputElement>(null);
  const [abierto, setAbierto] = useState<Entidad | null>(null);
  const [contenido, setContenido] = useState<string>("");

  const verArchivo = async (entidad: Entidad) => {
    if (abierto === entidad) return setAbierto(null);
    const datos = await api.leer<unknown>(entidad);
    const texto = JSON.stringify(datos, null, 2);
    setContenido(texto.length > 20_000 ? `${texto.slice(0, 20_000)}\n…` : texto);
    setAbierto(entidad);
  };

  const importar = async (evento: ChangeEvent<HTMLInputElement>) => {
    const archivos = Array.from(evento.target.files ?? []);
    evento.target.value = "";
    const conocidos = new Map((resumen?.archivos ?? []).map((a): [string, Entidad] => [a.archivo, a.entidad]));
    const importados: string[] = [];
    const ignorados: string[] = [];
    for (const archivo of archivos) {
      const entidad = conocidos.get(archivo.name);
      if (!entidad) {
        ignorados.push(archivo.name);
        continue;
      }
      try {
        await api.reemplazar(entidad, JSON.parse(await archivo.text()));
        importados.push(archivo.name);
      } catch (e) {
        ignorados.push(`${archivo.name} (${(e as Error).message})`);
      }
    }
    alImportar(
      [importados.length && `Importados: ${importados.join(", ")}.`, ignorados.length && `No importados: ${ignorados.join(", ")}.`]
        .filter(Boolean)
        .join(" ") || "No se seleccionó ningún archivo.",
    );
  };

  const exportar = async () => {
    if (!resumen) return;
    const paquete: Record<string, unknown> = {};
    for (const a of resumen.archivos.filter((x) => x.presente)) paquete[a.entidad] = await api.leer(a.entidad);
    const url = URL.createObjectURL(new Blob([JSON.stringify(paquete, null, 2)], { type: "application/json" }));
    const enlace = Object.assign(document.createElement("a"), { href: url, download: "instancia.json" });
    enlace.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Tarjeta
      titulo="Archivos"
      paso={1}
      acciones={
        <div className="grupo-botones">
          <button className="boton boton--primario boton--chico" onClick={() => entradaArchivos.current?.click()}>
            Importar JSON
          </button>
          <button className="boton boton--chico" onClick={exportar} disabled={!resumen}>
            Exportar todo
          </button>
          <input ref={entradaArchivos} type="file" accept=".json,application/json" multiple hidden onChange={importar} />
        </div>
      }
    >
      {error && <p className="mensaje mensaje--error">{error}</p>}
      <div className="lista-archivos">
        {resumen?.archivos.map((a) => (
          <div key={a.entidad}>
            <div className="archivo">
              <span className={`estado ${a.presente ? "estado--ok" : a.opcional ? "estado--neutro" : "estado--error"}`}>
                <span className="sr-only">{a.presente ? "presente" : "falta"}</span>
              </span>
              <span className="archivo__nombre">
                {a.archivo}
                {a.opcional && <span style={{ color: "var(--gris-500)", fontFamily: "var(--fuente)" }}> (opcional)</span>}
              </span>
              <span className="archivo__conteo">
                {!a.presente
                  ? a.opcional
                    ? "valores por defecto"
                    : "falta"
                  : a.registros !== null
                    ? `${a.registros} ${NOMBRE_REGISTRO[a.entidad]}`
                    : `tope ${resumen?.configuracion.max_creditos ?? 20} créditos`}
              </span>
              <button className="boton boton--chico" disabled={!a.presente} onClick={() => verArchivo(a.entidad)}>
                {abierto === a.entidad ? "Ocultar" : "Ver"}
              </button>
            </div>
            {abierto === a.entidad && <pre className="archivo__vista">{contenido}</pre>}
          </div>
        ))}
      </div>
    </Tarjeta>
  );
}

function Validacion({ resumen }: { resumen: ResumenDatos }) {
  const { errores, advertencias, problemas } = resumen.validacion;
  return (
    <Tarjeta titulo="Validación" paso={2}>
      <p>
        <span className={`estado ${errores ? "estado--error" : "estado--ok"}`}>
          {errores} {errores === 1 ? "error" : "errores"}
        </span>
        {" · "}
        <span className={`estado ${advertencias ? "estado--aviso" : "estado--neutro"}`}>
          {advertencias} {advertencias === 1 ? "advertencia" : "advertencias"}
        </span>
      </p>
      {errores > 0 && (
        <p className="mensaje mensaje--error" style={{ marginTop: 10 }}>
          Los errores impiden ejecutar. Una demanda mayor que los cupos solo genera una advertencia.
        </p>
      )}
      {problemas.length > 0 && (
        <ul className="problemas">
          {problemas.map((p, i) => (
            <li key={i}>
              <span className={`estado ${p.gravedad === "error" ? "estado--error" : "estado--aviso"}`} />
              <span>
                <span className="problemas__ruta">{[p.archivo, p.registro, p.campo].filter(Boolean).join(" › ")}</span>
                {" — "}
                {p.mensaje}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}

const ESCASEZ: { valor: Escasez; texto: string }[] = [
  { valor: "holgada", texto: "Holgada" },
  { valor: "ajustada", texto: "Ajustada" },
  { valor: "escasa", texto: "Escasa" },
];

function Generar({ alGenerar }: { alGenerar: (mensaje: string) => void }) {
  const [p, setP] = useState<ParametrosGeneracion>({
    estudiantes: 250,
    secciones: 96,
    porcentaje_trabaja: 0.2,
    escasez: "ajustada",
    semilla: 42,
  });
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cambiar = (campo: keyof ParametrosGeneracion) => (e: ChangeEvent<HTMLInputElement>) =>
    setP({ ...p, [campo]: campo === "porcentaje_trabaja" ? Number(e.target.value) / 100 : Number(e.target.value) });

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setOcupado(true);
    setError(null);
    try {
      const r = await api.generar(p);
      alGenerar(
        `Instancia generada con semilla ${p.semilla}.` + (r.respaldo ? ` Los archivos anteriores quedaron en data/.respaldos/${r.respaldo}.` : ""),
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setOcupado(false);
    }
  };

  return (
    <Tarjeta titulo="Generar instancia" paso={3} descripcion="Crea una instancia nueva a partir de una semilla. Se guarda una copia de los datos actuales.">
      <form onSubmit={enviar}>
        <div className="campos">
          <label className="campo">
            <span className="campo__etiqueta">Estudiantes</span>
            <input className="entrada" type="number" min={0} max={5000} value={p.estudiantes} onChange={cambiar("estudiantes")} />
          </label>
          <label className="campo">
            <span className="campo__etiqueta">Secciones</span>
            <input className="entrada" type="number" min={42} max={1000} value={p.secciones} onChange={cambiar("secciones")} />
          </label>
          <label className="campo">
            <span className="campo__etiqueta">% que trabaja</span>
            <input
              className="entrada"
              type="number"
              min={0}
              max={100}
              value={Math.round(p.porcentaje_trabaja * 100)}
              onChange={cambiar("porcentaje_trabaja")}
            />
          </label>
          <label className="campo">
            <span className="campo__etiqueta">Semilla</span>
            <input className="entrada" type="number" min={0} value={p.semilla} onChange={cambiar("semilla")} />
          </label>
        </div>
        <div className="campo" style={{ marginBottom: 18 }}>
          <span className="campo__etiqueta">Escasez de cupos</span>
          <Segmentado etiqueta="Escasez de cupos" opciones={ESCASEZ} valor={p.escasez} alCambiar={(escasez) => setP({ ...p, escasez })} />
        </div>
        {error && (
          <p className="mensaje mensaje--error" style={{ marginBottom: 12 }}>
            {error}
          </p>
        )}
        <button className="boton boton--primario" type="submit" disabled={ocupado}>
          {ocupado ? "Generando…" : "Generar y reemplazar datos"}
        </button>
      </form>
    </Tarjeta>
  );
}
