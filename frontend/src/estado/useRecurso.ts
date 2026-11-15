import { useCallback, useEffect, useState, type DependencyList } from "react";

export interface Recurso<T> {
  datos: T | null;
  error: string | null;
  cargando: boolean;
  recargar: () => void;
}

/** Carga datos asíncronos y descarta respuestas que llegan después de desmontar o cambiar dependencias. */
export function useRecurso<T>(cargar: () => Promise<T>, dependencias: DependencyList = []): Recurso<T> {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    cargar()
      .then((resultado) => {
        if (!vigente) return;
        setDatos(resultado);
        setError(null);
      })
      .catch((e: Error) => vigente && setError(e.message))
      .finally(() => vigente && setCargando(false));
    return () => {
      vigente = false;
    };
  }, [...dependencias, version]);

  const recargar = useCallback(() => setVersion((v) => v + 1), []);
  return { datos, error, cargando, recargar };
}
