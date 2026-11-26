#!/usr/bin/env bash
# Levanta la web sobre una COPIA de un ejemplo, sin tocar data/ ni data/ejemplos/.
#
#   ./ejemplo.sh               lista los ejemplos
#   ./ejemplo.sh demo          copia data/ejemplos/demo a $TMPDIR/asignador/vivo y arranca
#   ./ejemplo.sh oficial       lo mismo con data/ (la instancia de 250 estudiantes)
#
# Cada vez empieza de cero: borra la copia anterior. Lo que se guarde desde la web
# (preferencias, configuración, importar, generar) y las corridas quedan en
# $TMPDIR/asignador/, que se puede borrar sin riesgo.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")" && pwd)"
BASE="${TMPDIR:-/tmp}"
TRABAJO="${BASE%/}/asignador"

if [[ $# -eq 0 ]]; then
  echo "Uso: ./ejemplo.sh <nombre>"
  echo
  echo "  oficial               data/ (250 estudiantes, la instancia de la entrega)"
  for d in "$RAIZ"/data/ejemplos/*/; do
    nombre="$(basename "$d")"
    titulo="$(head -1 "$d/LEEME.md" 2>/dev/null | sed 's/^# //')"
    printf "  %-21s %s\n" "$nombre" "$titulo"
  done
  exit 0
fi

if [[ "$1" == "oficial" ]]; then
  ORIGEN="$RAIZ/data"
else
  ORIGEN="$RAIZ/data/ejemplos/$1"
fi
if [[ ! -f "$ORIGEN/estudiantes.json" ]]; then
  echo "No existe el ejemplo '$1'. Ejecute ./ejemplo.sh para ver la lista." >&2
  exit 1
fi

rm -rf "$TRABAJO"
mkdir -p "$TRABAJO/vivo" "$TRABAJO/resultados"
cp "$ORIGEN"/*.json "$TRABAJO/vivo/"
[[ -f "$ORIGEN/LEEME.md" ]] && cp "$ORIGEN/LEEME.md" "$TRABAJO/vivo/"

echo "→ Ejemplo:    $1"
echo "→ Datos:      $TRABAJO/vivo        (edite aquí los JSON)"
echo "→ Corridas:   $TRABAJO/resultados"
echo "→ Web:        http://localhost:5173"
echo

ASIGNADOR_DATOS="$TRABAJO/vivo" ASIGNADOR_RESULTADOS="$TRABAJO/resultados" exec "$RAIZ/dev.sh"
