#!/usr/bin/env bash
set -euo pipefail
# Per-boot demo CAN metrics exporter. No-ops when the file is not in this checkout.
export PATH="${HOME}/.local/bin:${PATH}"
if [ ! -f demo/exporter.py ]; then
  echo "demo/exporter.py not present; skipping exporter"
  exit 0
fi
mkdir -p /tmp/teslatoolbox
pkill -f 'demo/exporter.py' >/dev/null 2>&1 || true
nohup python3 demo/exporter.py >/tmp/teslatoolbox/exporter.log 2>&1 &
for _ in $(seq 1 20); do
  if curl -sf http://127.0.0.1:9105/metrics | grep -q tesla_can_signal; then
    echo "tesla-can-exporter ready on :9105"
    exit 0
  fi
  sleep 0.25
done
echo "exporter failed to become ready" >&2
cat /tmp/teslatoolbox/exporter.log >&2 || true
exit 1
