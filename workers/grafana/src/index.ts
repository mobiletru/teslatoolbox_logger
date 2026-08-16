import { renderDashboard } from "./ui";

const TESLA_PATHS = new Set([
  "/api/signals",
  "/api/signals/catalog",
  "/api/stream",
  "/metrics",
]);

function json(data: unknown, status = 200, extra: HeadersInit = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...extra,
    },
  });
}

function teslaTarget(request: Request, env: Env, pathname: string): Request {
  const search = new URL(request.url).search;
  const url = env.TESLA_SIGNALS
    ? new URL(pathname + search, "https://tesla-signals")
    : new URL(pathname + search, env.TESLA_SIGNALS_URL);
  return new Request(url, {
    method: request.method,
    headers: request.headers,
    redirect: "follow",
  });
}

async function proxyTesla(request: Request, env: Env, pathname: string): Promise<Response> {
  const target = teslaTarget(request, env, pathname);
  const upstream = env.TESLA_SIGNALS
    ? await env.TESLA_SIGNALS.fetch(target)
    : await fetch(target);
  const headers = new Headers(upstream.headers);
  headers.set("cache-control", "no-store");
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}

export default {
  async fetch(request, env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    try {
      if (path === "/api/health") {
        return json({
          ok: true,
          service: "grafana-mobileccs",
          host: url.hostname,
          upstream: env.TESLA_SIGNALS ? "tesla-signals" : env.TESLA_SIGNALS_URL,
          ts: new Date().toISOString(),
        });
      }

      if (TESLA_PATHS.has(path)) {
        return proxyTesla(request, env, path);
      }

      if (path.startsWith("/api/")) {
        return json({ ok: false, error: "Not found" }, 404);
      }

      if (request.method !== "GET" && request.method !== "HEAD") {
        return json({ ok: false, error: "Method not allowed" }, 405);
      }

      return new Response(renderDashboard(), {
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "no-store",
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "unknown_error";
      console.log(JSON.stringify({ type: "error", path, message }));
      return json({ ok: false, error: "Upstream unavailable" }, 502);
    }
  },
} satisfies ExportedHandler<Env>;
