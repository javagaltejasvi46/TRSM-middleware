/**
 * Scenario files bundled from ../scenarios at build time. The `trsm-yaml-as-data`
 * plugin in vite.config.ts parses each YAML into plain data (or `{ __parseError }`),
 * so no YAML parser is shipped to the browser. Kept separate from scenarios.ts so
 * the validation logic can be unit-tested with plain objects.
 */
export const SCENARIO_FILES = import.meta.glob('../../../scenarios/**/*.yaml', { import: 'default', eager: true }) as Record<string, unknown>;
