import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { ProveedorApp } from "./estado/ContextoApp";
import "./estilos/tokens.css";
import "./estilos/base.css";
import "./estilos/componentes.css";
import "./estilos/horario.css";

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <BrowserRouter>
      <ProveedorApp>
        <App />
      </ProveedorApp>
    </BrowserRouter>
  </StrictMode>,
);
