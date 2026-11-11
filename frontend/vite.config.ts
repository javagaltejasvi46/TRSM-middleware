import { defineConfig, type Plugin } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
import { parse } from 'yaml';

// The Evaluation page reads the versioned scenario files from the repo's top-level
// scenarios/ folder at build time, so it never keeps its own copy of them.
const scenariosDir = fileURLToPath(new URL('../scenarios', import.meta.url));

/**
 * Turn `*.yaml` imports into plain data at build time, so no YAML parser ships to
 * the browser. A file that fails to parse becomes `{ __parseError }` instead of
 * breaking the build, and the page reports it.
 */
function yamlAsData(): Plugin {
  return {
    name: 'trsm-yaml-as-data',
    transform(src, id) {
      if (!id.endsWith('.yaml')) return null;
      let data: unknown;
      try {
        data = parse(src);
      } catch (e) {
        data = { __parseError: (e as Error).message };
      }
      return { code: `export default ${JSON.stringify(data)};`, map: null };
    },
  };
}

export default defineConfig({
  plugins: [react(), yamlAsData()],
  server: {
    port: 5173,
    host: true,
    fs: {
      allow: ['.', scenariosDir],
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});
