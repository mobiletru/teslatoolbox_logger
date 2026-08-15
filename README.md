# teslatoolbox_logger

Grafana dashboard for **Tesla Toolbox 3 CAN Explorer** signals, plus a Playwright login helper for [toolbox.tesla.com](https://toolbox.tesla.com/).

Toolbox CAN Explorer plots historical vehicle CAN signals (VIN / Product ID, log availability, then search-and-overlay of names such as `BMS_socUI` and `DI_vehicleSpeed`). This repo mirrors that layout in Grafana using Prometheus metrics named `tesla_can_signal`.

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

Then open [http://localhost:3000](http://localhost:3000) (admin / `tesla`). The provisioned dashboard is **Tesla Toolbox CAN Explorer**.

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
