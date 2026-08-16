#!/usr/bin/env python3
"""Grafana dashboard for https://tesla.mobileccs.com/ Prometheus metrics."""

from __future__ import annotations

import json
from pathlib import Path

UID = "tesla-mobileccs-signal-viewer"
DS = {"type": "prometheus", "uid": "${datasource}"}


def expr(name: str) -> str:
    return f'tesla_toolbox3_signal{{name="{name}"}}'


def timeseries(panel_id: int, title: str, x: int, y: int, w: int, h: int, names: list[str], unit: str = "none") -> dict:
    return {
        "id": panel_id,
        "type": "timeseries",
        "title": title,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": DS,
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 12,
                    "spanNulls": True,
                    "showPoints": "never",
                    "lineWidth": 2,
                },
                "unit": unit,
                "color": {"mode": "palette-classic"},
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
        "targets": [
            {
                "datasource": DS,
                "expr": expr(n),
                "legendFormat": n,
                "refId": chr(65 + i),
            }
            for i, n in enumerate(names)
        ],
    }


def stat(panel_id: int, title: str, x: int, y: int, w: int, h: int, name: str, unit: str) -> dict:
    return {
        "id": panel_id,
        "type": "stat",
        "title": title,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": DS,
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "decimals": 1,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "text", "value": None}, {"color": "green", "value": 0}],
                },
            }
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"]},
            "colorMode": "background",
            "graphMode": "area",
        },
        "targets": [{"datasource": DS, "expr": expr(name), "legendFormat": name, "refId": "A"}],
    }


def row(panel_id: int, title: str, y: int) -> dict:
    return {
        "id": panel_id,
        "type": "row",
        "title": title,
        "gridPos": {"x": 0, "y": y, "w": 24, "h": 1},
        "collapsed": False,
        "panels": [],
    }


def dashboard() -> dict:
    panels = []
    pid = 1

    def nid() -> int:
        nonlocal pid
        v = pid
        pid += 1
        return v

    panels.append(row(nid(), "tesla.mobileccs.com overview", 0))
    kpis = [
        ("BatteryLevel", "percent"),
        ("PackVoltage", "volt"),
        ("PackCurrent", "amp"),
        ("HvacPower", "kwatt"),
        ("InsideTemp", "celsius"),
        ("OutsideTemp", "celsius"),
        ("Speed", "velocitymph"),
        ("Odometer", "lengthmi"),
    ]
    for i, (name, unit) in enumerate(kpis):
        panels.append(stat(nid(), name, (i % 8) * 3, 1, 3, 4, name, unit))

    panels.append(row(nid(), "Battery", 5))
    panels.append(timeseries(nid(), "SoC and charge limit", 0, 6, 12, 8, ["BatteryLevel", "ChargeLimitSoc"], "percent"))
    panels.append(timeseries(nid(), "Pack V / I", 12, 6, 12, 8, ["PackVoltage", "PackCurrent"]))
    panels.append(timeseries(nid(), "Charge amps", 0, 14, 12, 8, ["ChargeAmps"], "amp"))
    panels.append(
        {
            "id": nid(),
            "type": "stat",
            "title": "ChargeState",
            "gridPos": {"x": 12, "y": 14, "w": 12, "h": 8},
            "datasource": DS,
            "options": {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "background"},
            "targets": [
                {
                    "datasource": DS,
                    "expr": 'tesla_toolbox3_signal_info{name="ChargeState"}',
                    "legendFormat": "{{value}}",
                    "refId": "A",
                }
            ],
        }
    )

    panels.append(row(nid(), "HVAC", 22))
    panels.append(
        timeseries(
            nid(),
            "Cabin and ambient",
            0,
            23,
            12,
            8,
            ["InsideTemp", "OutsideTemp", "HvacLeftVentTemp", "HvacRightVentTemp", "EvaporatorTemp"],
            "celsius",
        )
    )
    panels.append(
        timeseries(
            nid(),
            "HVAC power",
            12,
            23,
            12,
            8,
            ["HvacPower", "CompressorPower", "PtcHeaterPower"],
            "kwatt",
        )
    )
    panels.append(
        timeseries(
            nid(),
            "Battery loop temps",
            0,
            31,
            12,
            8,
            ["CoolantTempBatt", "BatteryInletTemp", "BatteryOutletTemp"],
            "celsius",
        )
    )
    panels.append(timeseries(nid(), "Fan / humidity", 12, 31, 12, 8, ["HvacFanSpeed", "CabinHumidity"]))

    panels.append(row(nid(), "Tires / vehicle", 39))
    panels.append(
        timeseries(
            nid(),
            "TPMS",
            0,
            40,
            12,
            8,
            ["TpmsPressureFl", "TpmsPressureFr", "TpmsPressureRl", "TpmsPressureRr"],
            "pressurebar",
        )
    )
    panels.append(timeseries(nid(), "Speed / odometer", 12, 40, 12, 8, ["Speed", "Odometer"]))

    panels.append(row(nid(), "Signal picker", 48))
    panels.append(
        timeseries(
            nid(),
            "Selected signals ($signal)",
            0,
            49,
            24,
            10,
            [],
        )
    )
    panels[-1]["targets"] = [
        {
            "datasource": DS,
            "expr": 'tesla_toolbox3_signal{group=~"$group", name=~"$signal"}',
            "legendFormat": "{{name}}",
            "refId": "A",
        }
    ]

    return {
        "uid": UID,
        "title": "Tesla Toolbox 3 — tesla.mobileccs.com",
        "tags": ["tesla", "toolbox", "mobileccs"],
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "5s",
        "graphTooltip": 1,
        "editable": True,
        "time": {"from": "now-15m", "to": "now"},
        "templating": {
            "list": [
                {
                    "name": "datasource",
                    "type": "datasource",
                    "query": "prometheus",
                    "label": "Prometheus",
                    "hide": 0,
                    "current": {},
                },
                {
                    "name": "group",
                    "type": "query",
                    "datasource": DS,
                    "label": "Group",
                    "query": "label_values(tesla_toolbox3_signal, group)",
                    "refresh": 2,
                    "includeAll": True,
                    "allValue": ".*",
                    "sort": 1,
                },
                {
                    "name": "signal",
                    "type": "query",
                    "datasource": DS,
                    "label": "Signal",
                    "query": 'label_values(tesla_toolbox3_signal{group=~"$group"}, name)',
                    "refresh": 2,
                    "includeAll": True,
                    "allValue": ".*",
                    "multi": True,
                    "sort": 1,
                },
            ]
        },
        "annotations": {"list": []},
        "panels": panels,
        "links": [
            {
                "title": "tesla.mobileccs.com",
                "url": "https://tesla.mobileccs.com/",
                "type": "link",
                "icon": "external link",
                "targetBlank": True,
            },
            {
                "title": "/metrics",
                "url": "https://tesla.mobileccs.com/metrics",
                "type": "link",
                "icon": "bolt",
                "targetBlank": True,
            },
        ],
    }


def main() -> None:
    path = Path("grafana/dashboards/tesla-mobileccs-signal-viewer.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dashboard(), indent=2) + "\n")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
