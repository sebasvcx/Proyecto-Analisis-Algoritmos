import { NavLink } from "react-router-dom";
import { useApp } from "../estado/ContextoApp";

const PESTANAS = [
  { ruta: "/datos", texto: "Datos" },
  { ruta: "/estudiantes", texto: "Estudiantes" },
  { ruta: "/ejecutar", texto: "Ejecutar" },
  { ruta: "/resultados", texto: "Resultados" },
];

/** Barra con pestañas y selector de estudiante (la aplicación no tiene inicio de sesión). */
export function BarraSuperior() {
  const { estudiantes, estudianteActivo, seleccionarEstudiante } = useApp();

  return (
    <header className="barra">
      <div className="barra__contenido">
        <NavLink to="/datos" className="barra__marca">
          Asignador de horarios
        </NavLink>
        <nav className="barra__pestanas" aria-label="Secciones">
          {PESTANAS.map((p) => (
            <NavLink key={p.ruta} to={p.ruta} className="barra__pestana">
              {p.texto}
            </NavLink>
          ))}
        </nav>
        {estudiantes.length > 0 && (
          <label className="selector-estudiante">
            Estudiante:
            <select value={estudianteActivo?.id ?? ""} onChange={(e) => seleccionarEstudiante(e.target.value)}>
              {estudiantes.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.id} · {e.nombre}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
    </header>
  );
}
