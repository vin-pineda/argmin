/** Server-side proxy to the engine. Keeps the engine URL off the client and
 *  gives the browser a same-origin path (`/api/*`), per the no-login UX spec. */

const ENGINE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function proxy(
  path: string,
  init: RequestInit & { searchParams?: Record<string, string> } = {},
): Promise<Response> {
  const { searchParams, ...rest } = init;
  const url = new URL(path, ENGINE_URL);
  if (searchParams) {
    for (const [k, v] of Object.entries(searchParams)) url.searchParams.set(k, v);
  }
  try {
    const r = await fetch(url, {
      ...rest,
      headers: { "content-type": "application/json", ...(rest.headers ?? {}) },
      // engine runs are deterministic + cached engine-side; don't double-cache here
      cache: "no-store",
    });
    const text = await r.text();
    return new Response(text, {
      status: r.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return new Response(
      JSON.stringify({
        error: "engine_unreachable",
        detail: `Could not reach the Argmin engine at ${ENGINE_URL}. Start it with \`uv run uvicorn argmin.api:app\`.`,
      }),
      { status: 502, headers: { "content-type": "application/json" } },
    );
  }
}
