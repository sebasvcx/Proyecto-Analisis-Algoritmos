import { useEffect } from "react";
import { api } from "../api/cliente";
import type { CorridaResumida, Salida } from "../api/tipos";
import { useApp } from "./ContextoApp";
import { useRecurso, type Recurso } from "./useRecurso";

export interface CorridaActual extends Recurso<Salida | null> {
  corridas: CorridaResumida[];
}

/**
 * Corrida que se está consultando. Si no hay una elegida (o ya no existe),
 * se usa la más reciente de resultados/.
 */
export function useCorridaActual(): CorridaActual {
  const { corridaActiva, seleccionarCorrida } = useApp();
  const corridas = useRecurso(api.corridas);

  const existe = corridas.datos?.some((c) => c.id === corridaActiva) ?? false;
  const id = existe ? corridaActiva : (corridas.datos?.[0]?.id ?? null);

  useEffect(() => {
    if (corridas.datos && id !== corridaActiva) seleccionarCorrida(id);
  }, [corridas.datos, id, corridaActiva, seleccionarCorrida]);

  const salida = useRecurso<Salida | null>(() => (id ? api.corrida(id) : Promise.resolve(null)), [id]);
  return {
    ...salida,
    cargando: salida.cargando || corridas.cargando,
    corridas: corridas.datos ?? [],
  };
}
