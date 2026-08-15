#!/usr/bin/env python3
"""Demo Prometheus exporter that emits Tesla Toolbox CAN Explorer signal names.

This is synthetic drive-cycle data so the Grafana dashboard can be previewed
without a vehicle or Toolbox session.
"""

from __future__ import annotations

import math
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VIN = os.environ.get("TESLA_VIN", "5YJ3E1EA0KF000000")
BUS = os.environ.get("TESLA_CAN_BUS", "vehicle")
PORT = int(os.environ.get("EXPORTER_PORT", "9105"))

START = time.time()
frames = 0
decoded = 0
lock = threading.Lock()


def signal_values(now: float) -> dict[str, float]:
    t = now - START
    speed = max(0.0, 90.0 * math.sin(t / 40.0) ** 2)
    accel = max(0.0, min(100.0, 40.0 + 30.0 * math.sin(t / 8.0)))
    current = -speed * 1.1 - accel * 0.4 + 20.0 * math.sin(t / 5.0)
    voltage = 398.0 - abs(current) * 0.04
    soc = 72.0 - t / 1800.0
    pack_t = 28.0 + 3.0 * math.sin(t / 90.0)
    return {
        "BMS_socMin": soc - 0.8,
        "BMS_socUI": soc,
        "BMS_socMax": soc + 0.6,
        "BMS_socAvg": soc - 0.1,
        "BMS_packVoltage": voltage,
        "BMS_packCurrent": current,
        "BMS_maxDischargePower": 250.0,
        "BMS_maxRegenPower": 80.0,
        "BMS_nominalEnergyRemaining": soc / 100.0 * 75.0,
        "BMS_nominalFullPackEnergy": 75.0,
        "BMS_idealEnergyRemaining": soc / 100.0 * 78.0,
        "BMS_packTMin": pack_t - 1.5,
        "BMS_packTMax": pack_t + 2.0,
        "BMS_thermistorTMin": pack_t - 2.0,
        "BMS_thermistorTMax": pack_t + 2.5,
        "BMS_brickVoltageMin": 3.92,
        "BMS_brickVoltageMax": 4.01,
        "BMS_kwhDischargeTotal": 41230.0 + t / 3600.0,
        "BMS_kwhChargeTotal": 42810.0 + t / 7200.0,
        "BMS_kwhRegenChargeTotal": 6120.0 + t / 9000.0,
        "BMS_kwhDriveDischargeTotal": 35100.0 + t / 3600.0,
        "BMS_acChargePowerRequest": 0.0,
        "CP_evseOutputDcVoltage": 0.0,
        "CP_evseOutputDcCurrent": 0.0,
        "DI_vehicleSpeed": speed,
        "ESP_vehicleSpeed": speed * 1.01,
        "DI_accelPedalPos": accel,
        "DI_torqueCommand": current * -2.2,
        "DI_torqueActual": current * -2.1,
        "DI_motorRPM": speed * 95.0,
        "DI_brakeFLTemp": 45 + speed * 0.2,
        "DI_brakeFRTemp": 44 + speed * 0.2,
        "DI_brakeRLTemp": 40 + speed * 0.15,
        "DI_brakeRRTemp": 41 + speed * 0.15,
        "EPAS3P_internalSAS": 12.0 * math.sin(t / 6.0),
        "EPAS3P_torsionBarTorque": 2.0 * math.sin(t / 6.0),
        "UI_expectedRange": soc * 4.2,
        "VCFRONT_tempAmbient": 18.0 + 2.0 * math.sin(t / 200.0),
        "VCFRONT_tempCabin": 21.5,
        "VCFRONT_compressorTargetDuty": 35.0,
        "VCSEC_TPMSPressure0": 2.85,
        "VCSEC_TPMSPressure1": 2.88,
        "VCSEC_TPMSPressure2": 2.81,
        "VCSEC_TPMSPressure3": 2.83,
        "VCSEC_TPMSTemperature0": 24.0 + speed * 0.05,
        "VCSEC_TPMSTemperature1": 24.5 + speed * 0.05,
        "VCSEC_TPMSTemperature2": 26.0 + speed * 0.04,
        "VCSEC_TPMSTemperature3": 25.5 + speed * 0.04,
    }


def render() -> bytes:
    global frames, decoded
    now = time.time()
    with lock:
        frames += 2700
        decoded += 1100
        f_total, d_total = frames, decoded
    values = signal_values(now)
    lines = [
        "# HELP tesla_can_signal Decoded Tesla Toolbox CAN Explorer signal",
        "# TYPE tesla_can_signal gauge",
    ]
    for name, value in values.items():
        lines.append(
            f'tesla_can_signal{{vin="{VIN}",bus="{BUS}",signal="{name}"}} {value:.6f}'
        )
    lines += [
        "# HELP tesla_can_log_available Toolbox CAN Explorer log availability (1=available)",
        "# TYPE tesla_can_log_available gauge",
        f'tesla_can_log_available{{vin="{VIN}",bus="{BUS}"}} 1',
        "# HELP tesla_can_frames_total CAN frames observed",
        "# TYPE tesla_can_frames_total counter",
        f'tesla_can_frames_total{{vin="{VIN}",bus="{BUS}"}} {f_total}',
        "# HELP tesla_can_decoded_frames_total CAN frames decoded via DBC",
        "# TYPE tesla_can_decoded_frames_total counter",
        f'tesla_can_decoded_frames_total{{vin="{VIN}",bus="{BUS}"}} {d_total}',
        "# HELP tesla_can_unique_ids Distinct CAN IDs in the current window",
        "# TYPE tesla_can_unique_ids gauge",
        f'tesla_can_unique_ids{{vin="{VIN}",bus="{BUS}"}} 312',
        "",
    ]
    return ("\n".join(lines)).encode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path not in ("/metrics", "/"):
            self.send_error(404)
            return
        body = render()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Tesla CAN demo exporter on :{PORT}/metrics vin={VIN}")
    server.serve_forever()


if __name__ == "__main__":
    main()
