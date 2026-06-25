import scenarioJson from "@/data/default-scenario.json";

import type { DefaultScenario } from "./types";

/** The precomputed default scenario, baked at build time for instant first paint.
 *  Regenerate with `uv run argmin default-scenario` in the engine. */
export const defaultScenario = scenarioJson as unknown as DefaultScenario;
