import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/cliente";
import type { Configuracion, Nivel } from "../api/tipos";
import { Segmentado, Tarjeta } from "../componentes/Tarjeta";
import { useApp } from "../estado/ContextoApp";
import { useRecurso } from "../estado/useRecurso";
import { fechaCorta, porcentaje } from "../utilidades/formato";

export function PaginaEjecutar() {
  const navegar = useNavigate();
  const { estudiantes, seleccionarCorrida } = useApp();
  const niveles = useRecurso(api.niveles);
  const corridas = useRecurso(api.corridas);
  const resumen = useRecurso(api.resumenDatos);

  const [nivel, setNivel] = useState<number | null>(null);
  const [ejecutando, setEjecutando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Por defecto se propone el nivel más alto ya implementado
  useEffect(() => {
    if (nivel === null && niveles.datos) {
      const disponibles = niveles.datos.filter((n) => n.disponible);
      setNivel(disponibles.at(-1)?.numero ?? null);
    }
  }, [niveles.datos, nivel]);

  const errores = resumen.datos?.validacion.errores ?? 0;

  const ejecutar = async () => {
    if (nivel === null) return;
    setEjecutando(true);
    setError(null);
    try {
      const salida = await api.ejecutar(nivel);
      seleccionarCorrida(salida.corrida.id);
      navegar("/resultados");
    } catch (e) {
      setError((e as Error).message);
      setEjecutando(false);
    }
  };

  return (
    <main className="pagina">
      <div className="pagina__encabezado">
        <div>
          <h1>Ejecutar asignación</h1>
          <p className="pagina__subtitulo">Asigna secciones a los {estudiantes.length} estudiantes en una sola corrida.</p>
        </div>
      </div>

      <div className="rejilla rejilla--mitades">
        <div className="pila">
          {resumen.datos && <ConfiguracionUniversidad inicial={resumen.datos.configuracion} alGuardar={resumen.recargar} />}
          <Tarjeta titulo="Corridas anteriores">
            {corridas.datos?.length ? (
              <ul className="corridas">
                {corridas.datos.slice(0, 6).map((c) => (
                  <li key={c.id}>
                    <span>
                      Nivel {c.nivel} · {fechaCorta(c.fecha)} · cobertura {porcentaje(c.cobertura)}
                      {c.violaciones > 0 && <span className="estado estado--aviso"> {c.violaciones} violaciones</span>}
                    </span>
                    <button
                      className="boton boton--chico"
                      onClick={() => {
                        seleccionarCorrida(c.id);
                        navegar("/resultados");
                      }}
                    >
                      Ver
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="pagina__subtitulo">Todavía no hay corridas guardadas en resultados/.</p>
            )}
          </Tarjeta>
        </div>

        <div className="pila">
          <Tarjeta titulo="Nivel del algoritmo" paso={2} descripcion="Cada nivel incluye todos los anteriores.">
            {niveles.datos && <ListaNiveles niveles={niveles.datos} elegido={nivel} alElegir={setNivel} />}
          </Tarjeta>

          <Tarjeta>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span className="paso">3</span>
              <button className="boton boton--primario" onClick={ejecutar} disabled={ejecutando || nivel === null || errores > 0}>
                {ejecutando ? "Ejecutando…" : "Ejecutar corrida"}
              </button>
              {errores > 0 && <span className="estado estado--error">Corrija los {errores} errores de los datos</span>}
            </div>
            {ejecutando && (
              <div className="progreso" aria-label="Corrida en curso">
                <div className="progreso__relleno" />
              </div>
            )}
            {error && (
              <p className="mensaje mensaje--error" style={{ marginTop: 14 }}>
                {error}
              </p>
            )}
            <p className="pagina__subtitulo" style={{ marginTop: 12, fontSize: "0.88rem" }}>
              Validar datos → asignar → verificar reglas de forma independiente → guardar en <code>resultados/</code>.
            </p>
          </Tarjeta>
        </div>
      </div>
    </main>
  );
}

function ListaNiveles({ niveles, elegido, alElegir }: { niveles: Nivel[]; elegido: number | null; alElegir: (n: number) => void }) {
  return (
    <ul className="niveles" role="radiogroup" aria-label="Nivel del algoritmo">
      {niveles.map((n) => {
        const clases = ["nivel", n.numero === elegido && "nivel--elegido", !n.disponible && "nivel--bloqueado"].filter(Boolean).join(" ");
        return (
          <li key={n.numero}>
            <label className={clases} title={n.descripcion}>
              <input
                type="radio"
                name="nivel"
                checked={n.numero === elegido}
                disabled={!n.disponible}
                onChange={() => alElegir(n.numero)}
              />
              <span className="nivel__numero">N{n.numero}</span>
              <span>{n.nombre}</span>
              <span className="nivel__marca">{n.disponible ? n.reglas.join(" ") : "pendiente"}</span>
            </label>
          </li>
        );
      })}
    </ul>
  );
}

function ConfiguracionUniversidad({ inicial, alGuardar }: { inicial: Configuracion; alGuardar: () => void }) {
  const [c, setC] = useState<Configuracion>(inicial);
  const [estado, setEstado] = useState<"limpio" | "sucio" | "guardando" | "guardado">("limpio");

  const cambiar = (cambios: Partial<Configuracion>) => {
    setC({ ...c, ...cambios });
    setEstado("sucio");
  };

  const guardar = async () => {
    setEstado("guardando");
    await api.reemplazar("config", { ...inicial, ...c });
    setEstado("guardado");
    alGuardar();
  };

  return (
    <Tarjeta
      titulo="Configuración de la universidad"
      paso={1}
      acciones={
        <button className="boton boton--chico" onClick={guardar} disabled={estado !== "sucio"}>
          {estado === "guardado" ? "Guardado" : estado === "guardando" ? "Guardando…" : "Guardar"}
        </button>
      }
    >
      <div className="campos" style={{ gridTemplateColumns: "1fr" }}>
        <label className="campo">
          <span className="campo__etiqueta">Tope de créditos por estudiante</span>
          <input
            className="entrada"
            type="number"
            min={1}
            value={c.max_creditos ?? 20}
            onChange={(e) => cambiar({ max_creditos: Number(e.target.value) })}
          />
        </label>
        <div className="campo">
          <span className="campo__etiqueta">Prioridad por semestre (se usa en el nivel 10)</span>
          <Segmentado
            etiqueta="Prioridad por semestre"
            opciones={[
              { valor: true, texto: "Activa" },
              { valor: false, texto: "Inactiva" },
            ]}
            valor={c.desempate_semestre ?? false}
            alCambiar={(desempate_semestre) => cambiar({ desempate_semestre })}
          />
        </div>
        <label className="campo">
          <span className="campo__etiqueta">Valor de una materia sustituta (% de la original, desde el nivel 4)</span>
          <input
            className="entrada"
            type="number"
            min={0}
            max={100}
            value={Math.round((c.valor_sustituta ?? 0.8) * 100)}
            onChange={(e) => cambiar({ valor_sustituta: Number(e.target.value) / 100 })}
          />
        </label>
        <label className="campo">
          <span className="campo__etiqueta">Semilla</span>
          <input className="entrada" type="number" min={0} value={c.semilla ?? 42} onChange={(e) => cambiar({ semilla: Number(e.target.value) })} />
        </label>
      </div>
    </Tarjeta>
  );
}
