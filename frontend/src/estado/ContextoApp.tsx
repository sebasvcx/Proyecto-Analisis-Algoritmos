import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/cliente";
import type { Estudiante } from "../api/tipos";

interface ContextoAppValor {
  /** Lista de estudiantes de data/ (para el selector de la barra superior). */
  estudiantes: Estudiante[];
  estudianteActivo: Estudiante | null;
  seleccionarEstudiante: (id: string) => void;
  /** Corrida que se está consultando en Resultados y Horario. */
  corridaActiva: string | null;
  seleccionarCorrida: (id: string | null) => void;
  /** Vuelve a leer los datos tras importar o generar una instancia. */
  refrescarDatos: () => void;
  /** Falso mientras el backend no responde. */
  servidorDisponible: boolean;
}

const Contexto = createContext<ContextoAppValor | null>(null);

function leerPreferencia(clave: string): string | null {
  try {
    return localStorage.getItem(clave);
  } catch {
    return null;
  }
}

function guardarPreferencia(clave: string, valor: string | null) {
  try {
    if (valor === null) localStorage.removeItem(clave);
    else localStorage.setItem(clave, valor);
  } catch {
    /* almacenamiento no disponible: la preferencia solo dura la sesión */
  }
}

export function ProveedorApp({ children }: { children: ReactNode }) {
  const [estudiantes, setEstudiantes] = useState<Estudiante[]>([]);
  const [idActivo, setIdActivo] = useState<string | null>(() => leerPreferencia("estudiante"));
  const [corridaActiva, setCorridaActiva] = useState<string | null>(() => leerPreferencia("corrida"));
  const [version, setVersion] = useState(0);
  const [servidorDisponible, setServidorDisponible] = useState(true);

  // Se comprueba al iniciar; mientras el backend no responda se reintenta cada 4 s
  useEffect(() => {
    let vigente = true;
    let temporizador: ReturnType<typeof setTimeout> | undefined;
    const comprobar = async () => {
      try {
        await api.salud();
        if (vigente) setServidorDisponible(true);
      } catch {
        if (!vigente) return;
        setServidorDisponible(false);
        temporizador = setTimeout(comprobar, 4000);
      }
    };
    comprobar();
    return () => {
      vigente = false;
      clearTimeout(temporizador);
    };
  }, []);

  // Cuando el servidor vuelve se recargan los estudiantes
  useEffect(() => {
    api
      .estudiantes()
      .then((lista) => setEstudiantes([...lista].sort((a, b) => a.id.localeCompare(b.id))))
      .catch(() => setEstudiantes([]));
  }, [version, servidorDisponible]);

  const seleccionarEstudiante = useCallback((id: string) => {
    setIdActivo(id);
    guardarPreferencia("estudiante", id);
  }, []);

  const seleccionarCorrida = useCallback((id: string | null) => {
    setCorridaActiva(id);
    guardarPreferencia("corrida", id);
  }, []);

  const valor = useMemo<ContextoAppValor>(() => {
    const activo = estudiantes.find((e) => e.id === idActivo) ?? estudiantes[0] ?? null;
    return {
      estudiantes,
      estudianteActivo: activo,
      seleccionarEstudiante,
      corridaActiva,
      seleccionarCorrida,
      refrescarDatos: () => setVersion((v) => v + 1),
      servidorDisponible,
    };
  }, [estudiantes, idActivo, corridaActiva, seleccionarEstudiante, seleccionarCorrida, servidorDisponible]);

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useApp(): ContextoAppValor {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useApp debe usarse dentro de <ProveedorApp>");
  return valor;
}
