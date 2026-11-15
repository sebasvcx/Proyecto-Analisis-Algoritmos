import { Navigate, Route, Routes } from "react-router-dom";
import { BarraSuperior } from "./componentes/BarraSuperior";
import { EstadoVacio } from "./componentes/Tarjeta";
import { useApp } from "./estado/ContextoApp";
import { PaginaDatos } from "./paginas/Datos";
import { PaginaEjecutar } from "./paginas/Ejecutar";
import { PaginaEstudiantes } from "./paginas/Estudiantes";
import { PaginaHorario } from "./paginas/Horario";
import { PaginaResultados } from "./paginas/Resultados";

export function App() {
  const { servidorDisponible } = useApp();

  return (
    <div className="app">
      <BarraSuperior />
      {servidorDisponible ? (
        <Routes>
          <Route path="/" element={<Navigate to="/datos" replace />} />
          <Route path="/datos" element={<PaginaDatos />} />
          <Route path="/estudiantes" element={<PaginaEstudiantes />} />
          <Route path="/ejecutar" element={<PaginaEjecutar />} />
          <Route path="/resultados" element={<PaginaResultados />} />
          <Route path="/resultados/:estudianteId" element={<PaginaHorario />} />
          <Route path="*" element={<Navigate to="/datos" replace />} />
        </Routes>
      ) : (
        <SinServidor />
      )}
    </div>
  );
}

function SinServidor() {
  return (
    <main className="pagina">
      <EstadoVacio titulo="El servidor no responde">
        <p>La aplicación web necesita el backend en el puerto 8000. Desde la raíz del proyecto:</p>
        <pre className="archivo__vista" style={{ textAlign: "left", maxWidth: 520, margin: "16px auto 0" }}>
          {"cd backend\nsource .venv/bin/activate\nuvicorn api.main:app --reload"}
        </pre>
        <p style={{ marginTop: 14 }}>
          O todo junto con <code>./dev.sh</code>. Esta página se reconecta sola en cuanto el servidor esté arriba.
        </p>
      </EstadoVacio>
    </main>
  );
}
