#!/usr/bin/env bash
# Idempotent host provisioning for e-zapys.
# Safe to re-run: each step detects "already done" and skips.
#
# Usage (on the host, from any directory):
#   bash ~/e-zapys/deploy/setup.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SWAPFILE="/swapfile"
SWAP_SIZE="1G"
UNIT_SRC="$REPO_ROOT/deploy/e-zapys.service"
UNIT_DST="/etc/systemd/system/e-zapys.service"

echo "==> 1/5  Swap (${SWAP_SIZE} at ${SWAPFILE})"
if swapon --show=NAME --noheadings | grep -qx "${SWAPFILE}"; then
  echo "    already active — skipping"
else
  sudo fallocate -l "$SWAP_SIZE" "$SWAPFILE"
  sudo chmod 600 "$SWAPFILE"
  sudo mkswap "$SWAPFILE"
  sudo swapon "$SWAPFILE"
  grep -q "^${SWAPFILE} " /etc/fstab \
    || echo "${SWAPFILE} none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
  echo "    created"
fi
free -h | awk 'NR==1 || /^Swap/'

echo "==> 2/5  System packages"
sudo apt-get update -y -qq
sudo apt-get install -y -qq python3 python3-venv xvfb

echo "==> 3/5  Python venv + Python deps"
cd "$REPO_ROOT"
[ -d venv ] || python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo "==> 4/5  Playwright + Chromium"
sudo ./venv/bin/playwright install-deps chromium
./venv/bin/playwright install chromium

echo "==> 5/5  systemd unit"
sudo install -m 0644 -o root -g root "$UNIT_SRC" "$UNIT_DST"
sudo systemctl daemon-reload
sudo systemctl enable e-zapys
sudo systemctl restart e-zapys
sleep 3
sudo systemctl status --no-pager -n 15 e-zapys || true

echo
echo "Done. Tail logs with:"
echo "    sudo journalctl -u e-zapys -f"
