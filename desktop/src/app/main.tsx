import "./styles/global.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { QueryProvider } from "./providers/QueryProvider";
import { AppRouter } from "./router/AppRouter";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("index.html has no #root element");
}

createRoot(root).render(
  <StrictMode>
    <QueryProvider>
      <AppRouter />
    </QueryProvider>
  </StrictMode>,
);
