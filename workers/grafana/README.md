# grafana.mobileccs.com

Cloudflare Worker serving a Grafana-style dashboard for Tesla Toolbox 3 signals.

- Worker name: `grafana`
- Account: `mobileclimatre` (`bb21a9b692b753b16ebbdf537f174909`)
- Custom Domain: `grafana.mobileccs.com`
- Fallback: `https://grafana.ben-bb2.workers.dev`

## Deploy

```bash
npm install
npx wrangler deploy
```

`npm install` runs `wrangler types`, which writes the generated `worker-configuration.d.ts`. That file is not committed.

Useful checks:

```bash
npx wrangler deploy --dry-run   # bundle without publishing
npx tsc --noEmit                # typecheck
npx wrangler tail               # live logs
npx wrangler rollback           # revert to previous version
```

## Routing

`wrangler.jsonc` declares `grafana.mobileccs.com` as a Custom Domain, so Cloudflare creates the DNS record and certificate on deploy. Before the first deploy the hostname did not resolve at all.

## Upstream

Signal data comes from the `tesla-signals` Worker through the `TESLA_SIGNALS` service binding, which stays inside Cloudflare rather than going back out over the internet. `TESLA_SIGNALS_URL` is only a fallback for local `wrangler dev`, where the binding is not available.

Proxied paths are `/api/signals`, `/api/signals/catalog`, `/api/stream`, and `/metrics`. Everything else under `/api/` returns 404; any other path returns the dashboard HTML.

## Data is demo, not a vehicle

`tesla-signals` sets `source = "toolbox3-demo"` as a constant and simulates every value in-Worker. It exposes no ingest endpoint and reads no configuration, so this dashboard cannot show real telemetry as things stand, and the demo catalog contains no DI motor currents (`DIF_motorCurrent`, `DIREL_motorCurrent`, `DIRER_motorCurrent`).

Going live needs one of:

1. An authenticated ingest endpoint on `tesla-signals` plus KV or a Durable Object holding the newest sample, so an external collector can push real readings.
2. A gateway holding a Toolbox 3 session that forwards the CAN Explorer `signals` API.

Either collector has to run somewhere Tesla SSO is reachable. `auth.tesla.com` returns Akamai Access Denied from datacenter IPs, so it needs the shop network.

## Layout

| File | Purpose |
| --- | --- |
| `src/index.ts` | Routing, health, upstream proxy |
| `src/ui.ts` | Dashboard HTML, CSS, and canvas charts |
| `wrangler.jsonc` | Name, Custom Domain, service binding, observability |
