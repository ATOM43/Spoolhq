// @ts-check
import js from "@eslint/js";
import boundaries from "eslint-plugin-boundaries";
import { defineConfig } from "eslint/config";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["node_modules/", "dist/", "coverage/"] },
  js.configs.recommended,
  // Type-aware rules catch floating promises and unsafe `any` use.
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [
      reactHooks.configs.flat["recommended-latest"],
      reactRefresh.configs.vite,
    ],
    languageOptions: { globals: globals.browser },
  },
  // Feature-Sliced Design: app → pages → widgets → features → entities → shared.
  // A slice may import only from lower layers, only through their index.ts, and
  // never from another slice on its own layer. See README.md.
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: { boundaries },
    settings: {
      "import/resolver": { typescript: { project: "./tsconfig.json" } },
      "boundaries/elements": [
        { type: "app", pattern: "src/app" },
        ...["pages", "widgets", "features", "entities"].map((layer) => ({
          type: layer,
          pattern: `src/${layer}/*`,
          capture: ["slice"],
        })),
        { type: "shared", pattern: "src/shared/*", capture: ["segment"] },
      ],
    },
    rules: {
      "boundaries/no-unknown-files": "error",
      "boundaries/dependencies": [
        "error",
        {
          default: "disallow",
          policies: [
            // Packages from node_modules are not governed by the layer rules.
            { allow: { to: { module: { origin: ["external", "core"] } } } },
            // Files inside one slice import each other freely.
            {
              allow: { dependency: { relationship: { to: "internal" } } },
            },
            ...layerPolicies({
              app: ["pages", "widgets", "features", "entities", "shared"],
              pages: ["widgets", "features", "entities", "shared"],
              widgets: ["features", "entities", "shared"],
              features: ["entities", "shared"],
              entities: ["shared"],
              shared: ["shared"],
            }),
          ],
        },
      ],
    },
  },
  {
    files: ["**/*.js"],
    extends: [tseslint.configs.disableTypeChecked],
  },
);

/**
 * One policy per layer: it may import the public API (index.ts) of the listed layers.
 * @param {Record<string, string[]>} allowed
 */
function layerPolicies(allowed) {
  return Object.entries(allowed).map(([from, to]) => ({
    from: { element: { type: from } },
    allow: {
      to: { element: { types: { anyOf: to }, fileInternalPath: "index.ts" } },
    },
  }));
}
