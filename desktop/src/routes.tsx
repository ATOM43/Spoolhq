import type { RouteObject } from "react-router";

import { Home } from "./routes/Home";
import { Layout } from "./routes/Layout";
import { ProjectPanel } from "./routes/ProjectPanel";

export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Home /> },
      { path: "/p/:id", element: <ProjectPanel /> },
    ],
  },
];
