#!/usr/bin/env bash
# Sync the laptop working tree to the host and restart the bot.
# Run from anywhere on the laptop:
#   bash deploy/sync.sh
set -euo pipefail

HOST="${E_ZAPYS_HOST:-instance-for-mia-centers-bot}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_DIR="e-zapys"

echo "==> rsync ${LOCAL_DIR} -> ${HOST}:${REMOTE_DIR}"
rsync -avh --delete \
  --exclude='.env' --exclude='.env.en' --exclude='.env.uk' \
  --exclude='venv/' --exclude='__pycache__/' --exclude='*.pyc' \
  "${LOCAL_DIR}/" "${HOST}:${REMOTE_DIR}/"

echo "==> refresh Python deps if requirements changed"
ssh "$HOST" "cd ${REMOTE_DIR} && ./venv/bin/pip install -q -r requirements.txt" || true

echo "==> restart service (if installed)"
if ssh "$HOST" "systemctl list-unit-files e-zapys.service --no-legend" | grep -q e-zapys; then
  ssh "$HOST" "sudo systemctl restart e-zapys && sudo systemctl status --no-pager -n 10 e-zapys"
else
  echo "e-zapys.service not installed yet — run: ssh $HOST 'bash ~/e-zapys/deploy/setup.sh'"
fi
