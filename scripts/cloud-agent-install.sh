#!/usr/bin/env bash
set -euo pipefail
# Idempotent Cloud Agent install. Safe on main (README-only) and on feature branches.
export PATH="${HOME}/.local/bin:${PATH}"
python3 -m pip install --user --upgrade pip
python3 -m pip install --user playwright
python3 -m playwright install chromium
if [ -f requirements.txt ]; then
  python3 -m pip install --user -r requirements.txt
fi
if [ -f scripts/generate_dashboard.py ]; then
  python3 scripts/generate_dashboard.py
fi
if [ -f scripts/toolbox_login.py ]; then
  python3 -m py_compile scripts/toolbox_login.py
fi
if [ -f demo/exporter.py ]; then
  python3 -m py_compile demo/exporter.py
fi
