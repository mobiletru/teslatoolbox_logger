# teslatoolbox_logger

Grafana dashboard for **Tesla Toolbox 3 CAN Explorer** signals, plus a Playwright login helper for [toolbox.tesla.com](https://toolbox.tesla.com/).

Toolbox CAN Explorer plots historical vehicle CAN signals (VIN / Product ID, log availability, then search-and-overlay of names such as `BMS_socUI` and `DI_vehicleSpeed`). This repo mirrors that layout in Grafana using Prometheus metrics named `tesla_can_signal`.

## Live: grafana.mobileccs.com

[https://grafana.mobileccs.com](https://grafana.mobileccs.com) is deployed from [`workers/grafana`](workers/grafana). It serves a Grafana-style live dashboard and proxies the signal API of the `tesla-signals` Worker over a service binding, so no Prometheus or Docker is required to view current values.

| Path | Serves |
| --- | --- |
| `/` | Dashboard: KPI stats, four live charts, signal picker |
| `/api/health` | Worker health and which upstream is in use |
| `/api/signals`, `/api/signals/catalog` | Current snapshot and signal catalog |
| `/api/stream` | Server-sent events, ~4 Hz |
| `/metrics` | Prometheus `tesla_toolbox3_signal` passthrough |

See [`workers/grafana/README.md`](workers/grafana/README.md) for deploy and configuration.

**The data is synthetic.** `tesla-signals` hardcodes `source = "toolbox3-demo"` and generates its values in-Worker, so `grafana.mobileccs.com` shows simulated HVAC, battery, and tire signals rather than a vehicle. The demo catalog has no DI motor currents. Serving real readings requires a Toolbox 3 gateway.

## Playwright login (Toolbox 3)

Tesla SSO lives at `auth.tesla.com` behind Akamai. Datacenter IPs (including this Cursor cloud agent, `34.214.152.11`) are **Access Denied**. Run login from a shop or home network that can open Toolbox in Chrome.

```bash
pip install -r requirements.txt
python -m playwright install chromium

export TESLA_TOOLBOX_EMAIL='you@shop.example'
export TESLA_TOOLBOX_PASSWORD='…'
export TESLA_TOOLBOX_OTP='123456'   # only if MFA is on

python scripts/toolbox_login.py --headed
```

A successful login writes `.toolbox-session.json` for later CAN Explorer automation. Do not commit that file.

## Preview the Grafana dashboard (demo data)

No vehicle required. Synthetic Toolbox signal names are exported on `:9105/metrics`.

```bash
python scripts/generate_dashboard.py
docker compose up -d
```

Then open [http://localhost:3000](http://localhost:3000) (admin / `tesla`). Provisioned dashboards:

- **Tesla Toolbox 3 — tesla.mobileccs.com** scrapes live Prometheus from [https://tesla.mobileccs.com/metrics](https://tesla.mobileccs.com/metrics) (`tesla_toolbox3_signal`). That Worker is currently `toolbox3-demo` (synthetic HVAC/battery), not a live car, until a Toolbox 3 gateway is configured.
- **Tesla Toolbox CAN Explorer** uses local demo exporter `:9105` with CAN Explorer names (`BMS_socUI`, …).

## Metric shape

```text
tesla_can_signal{vin="5YJ…",bus="vehicle",signal="BMS_packVoltage"} 398.12
tesla_can_log_available{vin="5YJ…",bus="vehicle"} 1
```

Dashboard variables match Toolbox: **VIN / Product ID**, **CAN bus**, and a **signal** picker (regex search, same idea as Toolbox `BMS.*current`).

## Panels

| Row | Signals |
| --- | --- |
| Overview | SoC, pack V/I/kW, speed, range, pack temp, cell ΔV, log availability |
| BMS | `BMS_soc*`, `BMS_hvBusStatus`, energy remaining, power limits |
| Thermal | `BMS_thermalStatus`, cabin/HVAC |
| Drive | `DI_vehicleSpeed`, pedals, torque, EPAS, brake temps |
| Charging | PCS/CP request, lifetime kWh counters |
| Tires | `VCSEC_TPMS*` |
| Signal picker | overlay any decoded Toolbox signal |
| Logger health | frames/s, unique IDs, decode ratio |

Signal names follow community Model 3/Y DBC maps that match Toolbox CAN Explorer (`BMS_packVoltage` on `0x132`, `BMS_socUI` on `0x292`, and so on).
