import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config.ts";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      include: ["src/**/*.test.{ts,tsx}"],
      setupFiles: ["src/shared/lib/test-setup.ts"],
      restoreMocks: true,
      // Reported by `vitest run --coverage` (`just test`); no threshold yet.
      coverage: {
        provider: "v8",
        include: ["src/**/*.{ts,tsx}"],
        exclude: ["src/**/*.test.{ts,tsx}", "src/shared/lib/test-setup.ts"],
        reporter: ["text"],
      },
    },
  }),
);
