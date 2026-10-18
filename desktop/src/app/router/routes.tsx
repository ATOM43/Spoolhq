import type { RouteObject } from "react-router";

import { HomePage } from "@/pages/home";
import { ProjectPanelPage } from "@/pages/project-panel";

import { RootLayout } from "./RootLayout";

export const routes: RouteObject[] = [
  {
    element: <RootLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/p/:id", element: <ProjectPanelPage /> },
    ],
  },
];
