#!/usr/bin/env python3
"""Generate the Grafana dashboard for Tesla Toolbox CAN Explorer signals."""

from __future__ import annotations

import json
from pathlib import Path

UID = "tesla-toolbox-can-explorer"
DS = {"type": "prometheus", "uid": "${datasource}"}
SELECTOR = 'vin=~"$vin", bus=~"$bus"'


def expr(signal: str) -> str:
    return f'tesla_can_signal{{{SELECTOR}, signal="{signal}"}}'


def timeseries(panel_id: int, title: str, x: int, y: int, w: int, h: int, targets: list[dict], unit: str = "none") -> dict:
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
            },
            "overrides": [],
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
        "targets": [
            {
                "datasource": DS,
                "expr": t["expr"],
                "legendFormat": t.get("legend", "{{signal}}"),
                "refId": chr(65 + i),
            }
            for i, t in enumerate(targets)
        ],
    }


def stat(panel_id: int, title: str, x: int, y: int, w: int, h: int, expr_str: str, unit: str, legend: str = "{{signal}}") -> dict:
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
                "color": {"mode": "thresholds"},
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "text", "value": None},
                        {"color": "green", "value": 0},
                    ],
                },
            }
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": "background",
            "graphMode": "area",
            "textMode": "value_and_name",
            "orientation": "auto",
        },
        "targets": [{"datasource": DS, "expr": expr_str, "legendFormat": legend, "refId": "A"}],
    }


def gauge(panel_id: int, title: str, x: int, y: int, w: int, h: int, expr_str: str, unit: str, max_value: float, steps: list[dict]) -> dict:
    return {
        "id": panel_id,
        "type": "gauge",
        "title": title,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": DS,
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "min": 0,
                "max": max_value,
                "thresholds": {"mode": "absolute", "steps": steps},
            }
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
        },
        "targets": [{"datasource": DS, "expr": expr_str, "legendFormat": "{{signal}}", "refId": "A"}],
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
    panels: list[dict] = []
    pid = 1

    def next_id() -> int:
        nonlocal pid
        value = pid
        pid += 1
        return value

    panels.append(row(next_id(), "Toolbox overview", 0))
    kpis = [
        ("SoC UI", expr("BMS_socUI"), "percent"),
        ("Pack voltage", expr("BMS_packVoltage"), "volt"),
        ("Pack current", expr("BMS_packCurrent"), "amp"),
        ("Pack power", f'{expr("BMS_packVoltage")} * {expr("BMS_packCurrent")} / 1000', "kwatt"),
        ("Speed", expr("DI_vehicleSpeed"), "velocitykmh"),
        ("Range", expr("UI_expectedRange"), "lengthkm"),
        ("Pack T min", expr("BMS_packTMin"), "celsius"),
        ("Cell ΔV", f'{expr("BMS_brickVoltageMax")} - {expr("BMS_brickVoltageMin")}', "volt"),
    ]
    for i, (title, e, unit) in enumerate(kpis):
        panels.append(stat(next_id(), title, (i % 8) * 3, 1, 3, 4, e, unit, title))

    panels.append(
        gauge(
            next_id(),
            "BMS_socUI",
            0,
            5,
            6,
            7,
            expr("BMS_socUI"),
            "percent",
            100,
            [
                {"color": "red", "value": None},
                {"color": "orange", "value": 15},
                {"color": "green", "value": 30},
            ],
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Log availability (Toolbox CAN Explorer)",
            6,
            5,
            18,
            7,
            [
                {
                    "expr": f'tesla_can_log_available{{{SELECTOR}}}',
                    "legend": "Available",
                }
            ],
            unit="short",
        )
    )

    panels.append(row(next_id(), "Battery / BMS", 12))
    panels.append(
        timeseries(
            next_id(),
            "State of charge",
            0,
            13,
            12,
            8,
            [
                {"expr": expr("BMS_socMin"), "legend": "BMS_socMin"},
                {"expr": expr("BMS_socUI"), "legend": "BMS_socUI"},
                {"expr": expr("BMS_socMax"), "legend": "BMS_socMax"},
                {"expr": expr("BMS_socAvg"), "legend": "BMS_socAvg"},
            ],
            unit="percent",
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Pack voltage & current (0x132 BMS_hvBusStatus)",
            12,
            13,
            12,
            8,
            [
                {"expr": expr("BMS_packVoltage"), "legend": "BMS_packVoltage"},
                {"expr": expr("BMS_packCurrent"), "legend": "BMS_packCurrent"},
            ],
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Instantaneous pack power",
            0,
            21,
            12,
            8,
            [
                {
                    "expr": f'{expr("BMS_packVoltage")} * {expr("BMS_packCurrent")} / 1000',
                    "legend": "kW (V×I)",
                },
                {"expr": expr("BMS_maxDischargePower"), "legend": "BMS_maxDischargePower"},
                {"expr": expr("BMS_maxRegenPower"), "legend": "BMS_maxRegenPower"},
            ],
            unit="kwatt",
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Energy remaining",
            12,
            21,
            12,
            8,
            [
                {"expr": expr("BMS_nominalEnergyRemaining"), "legend": "BMS_nominalEnergyRemaining"},
                {"expr": expr("BMS_nominalFullPackEnergy"), "legend": "BMS_nominalFullPackEnergy"},
                {"expr": expr("BMS_idealEnergyRemaining"), "legend": "BMS_idealEnergyRemaining"},
            ],
            unit="kwatth",
        )
    )

    panels.append(row(next_id(), "Thermal", 29))
    panels.append(
        timeseries(
            next_id(),
            "Pack temperatures (0x312 BMS_thermalStatus)",
            0,
            30,
            12,
            8,
            [
                {"expr": expr("BMS_packTMin"), "legend": "BMS_packTMin"},
                {"expr": expr("BMS_packTMax"), "legend": "BMS_packTMax"},
                {"expr": expr("BMS_thermistorTMin"), "legend": "BMS_thermistorTMin"},
                {"expr": expr("BMS_thermistorTMax"), "legend": "BMS_thermistorTMax"},
            ],
            unit="celsius",
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Cabin / HVAC",
            12,
            30,
            12,
            8,
            [
                {"expr": expr("VCFRONT_tempAmbient"), "legend": "VCFRONT_tempAmbient"},
                {"expr": expr("VCFRONT_tempCabin"), "legend": "VCFRONT_tempCabin"},
                {"expr": expr("VCFRONT_compressorTargetDuty"), "legend": "VCFRONT_compressorTargetDuty"},
            ],
        )
    )

    panels.append(row(next_id(), "Drive", 38))
    panels.append(
        timeseries(
            next_id(),
            "Speed and pedals",
            0,
            39,
            12,
            8,
            [
                {"expr": expr("DI_vehicleSpeed"), "legend": "DI_vehicleSpeed"},
                {"expr": expr("DI_accelPedalPos"), "legend": "DI_accelPedalPos"},
                {"expr": expr("ESP_vehicleSpeed"), "legend": "ESP_vehicleSpeed"},
            ],
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Torque and motor (0x108 DI_torque)",
            12,
            39,
            12,
            8,
            [
                {"expr": expr("DI_torqueCommand"), "legend": "DI_torqueCommand"},
                {"expr": expr("DI_torqueActual"), "legend": "DI_torqueActual"},
                {"expr": expr("DI_motorRPM"), "legend": "DI_motorRPM"},
            ],
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Steering (EPAS3P)",
            0,
            47,
            12,
            8,
            [
                {"expr": expr("EPAS3P_internalSAS"), "legend": "EPAS3P_internalSAS"},
                {"expr": expr("EPAS3P_torsionBarTorque"), "legend": "EPAS3P_torsionBarTorque"},
            ],
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Brake temperatures",
            12,
            47,
            12,
            8,
            [
                {"expr": expr("DI_brakeFLTemp"), "legend": "FL"},
                {"expr": expr("DI_brakeFRTemp"), "legend": "FR"},
                {"expr": expr("DI_brakeRLTemp"), "legend": "RL"},
                {"expr": expr("DI_brakeRRTemp"), "legend": "RR"},
            ],
            unit="celsius",
        )
    )

    panels.append(row(next_id(), "Charging", 55))
    panels.append(
        timeseries(
            next_id(),
            "Charge request / EVSE",
            0,
            56,
            12,
            8,
            [
                {"expr": expr("BMS_acChargePowerRequest"), "legend": "BMS_acChargePowerRequest"},
                {"expr": expr("CP_evseOutputDcVoltage"), "legend": "CP_evseOutputDcVoltage"},
                {"expr": expr("CP_evseOutputDcCurrent"), "legend": "CP_evseOutputDcCurrent"},
            ],
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Lifetime energy counters (0x3D2 / 0x3F2)",
            12,
            56,
            12,
            8,
            [
                {"expr": expr("BMS_kwhDischargeTotal"), "legend": "BMS_kwhDischargeTotal"},
                {"expr": expr("BMS_kwhChargeTotal"), "legend": "BMS_kwhChargeTotal"},
                {"expr": expr("BMS_kwhRegenChargeTotal"), "legend": "BMS_kwhRegenChargeTotal"},
                {"expr": expr("BMS_kwhDriveDischargeTotal"), "legend": "BMS_kwhDriveDischargeTotal"},
            ],
            unit="kwatth",
        )
    )

    panels.append(row(next_id(), "Tires (VCSEC_TPMS)", 64))
    panels.append(
        timeseries(
            next_id(),
            "TPMS pressure",
            0,
            65,
            12,
            8,
            [
                {"expr": expr("VCSEC_TPMSPressure0"), "legend": "TPMS 0"},
                {"expr": expr("VCSEC_TPMSPressure1"), "legend": "TPMS 1"},
                {"expr": expr("VCSEC_TPMSPressure2"), "legend": "TPMS 2"},
                {"expr": expr("VCSEC_TPMSPressure3"), "legend": "TPMS 3"},
            ],
            unit="pressurebar",
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "TPMS temperature",
            12,
            65,
            12,
            8,
            [
                {"expr": expr("VCSEC_TPMSTemperature0"), "legend": "TPMS 0"},
                {"expr": expr("VCSEC_TPMSTemperature1"), "legend": "TPMS 1"},
                {"expr": expr("VCSEC_TPMSTemperature2"), "legend": "TPMS 2"},
                {"expr": expr("VCSEC_TPMSTemperature3"), "legend": "TPMS 3"},
            ],
            unit="celsius",
        )
    )

    panels.append(row(next_id(), "CAN Explorer signal picker", 73))
    panels.append(
        timeseries(
            next_id(),
            "Selected signal ($signal) — Toolbox-style overlay",
            0,
            74,
            24,
            10,
            [
                {
                    "expr": f'tesla_can_signal{{{SELECTOR}, signal=~"$signal"}}',
                    "legend": "{{signal}}",
                }
            ],
        )
    )

    panels.append(row(next_id(), "Logger health", 84))
    panels.append(
        timeseries(
            next_id(),
            "CAN frames / s",
            0,
            85,
            8,
            7,
            [
                {
                    "expr": f'rate(tesla_can_frames_total{{{SELECTOR}}}[$__rate_interval])',
                    "legend": "{{bus}}",
                }
            ],
            unit="cps",
        )
    )
    panels.append(
        stat(
            next_id(),
            "Unique CAN IDs",
            8,
            85,
            8,
            7,
            f'tesla_can_unique_ids{{{SELECTOR}}}',
            "short",
            "{{bus}}",
        )
    )
    panels.append(
        timeseries(
            next_id(),
            "Decode rate",
            16,
            85,
            8,
            7,
            [
                {
                    "expr": (
                        f'rate(tesla_can_decoded_frames_total{{{SELECTOR}}}[$__rate_interval]) '
                        f'/ rate(tesla_can_frames_total{{{SELECTOR}}}[$__rate_interval])'
                    ),
                    "legend": "decoded / total",
                }
            ],
            unit="percentunit",
        )
    )

    return {
        "uid": UID,
        "title": "Tesla Toolbox CAN Explorer",
        "tags": ["tesla", "toolbox", "can", "bms"],
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "5s",
        "graphTooltip": 1,
        "editable": True,
        "time": {"from": "now-15m", "to": "now"},
        "timepicker": {
            "refresh_intervals": ["1s", "5s", "10s", "30s", "1m", "5m"],
        },
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
                    "name": "vin",
                    "type": "query",
                    "datasource": DS,
                    "label": "VIN / Product ID",
                    "query": "label_values(tesla_can_signal, vin)",
                    "refresh": 2,
                    "includeAll": False,
                    "multi": False,
                    "sort": 1,
                },
                {
                    "name": "bus",
                    "type": "query",
                    "datasource": DS,
                    "label": "CAN bus",
                    "query": "label_values(tesla_can_signal{vin=~\"$vin\"}, bus)",
                    "refresh": 2,
                    "includeAll": True,
                    "allValue": ".*",
                    "multi": False,
                    "sort": 1,
                },
                {
                    "name": "signal",
                    "type": "query",
                    "datasource": DS,
                    "label": "Signal (Toolbox search)",
                    "query": "label_values(tesla_can_signal{vin=~\"$vin\", bus=~\"$bus\"}, signal)",
                    "refresh": 2,
                    "includeAll": True,
                    "allValue": "BMS_.*|DI_.*",
                    "multi": True,
                    "sort": 1,
                },
            ]
        },
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard",
                }
            ]
        },
        "panels": panels,
        "links": [
            {
                "title": "Tesla Toolbox 3",
                "url": "https://toolbox.tesla.com/",
                "type": "link",
                "icon": "external link",
                "targetBlank": True,
            }
        ],
    }


def main() -> None:
    path = Path("grafana/dashboards/tesla-toolbox-can-explorer.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dashboard(), indent=2) + "\n")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
