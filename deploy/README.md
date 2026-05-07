# Deploy

Single-host deployment for e-zapys on `instance-for-mia-centers-bot` (AWS EC2,
914 MiB RAM, 1 GiB swap added by `setup.sh`). Bot runs under systemd as a
service that auto-restarts on failure and is cgroup-capped so a runaway
Chromium can't take down the whole user session.

## First-time provisioning (run once on host)

```bash
ssh instance-for-mia-centers-bot 'bash ~/e-zapys/deploy/setup.sh'
```

`setup.sh` is idempotent: creates the swap file, installs apt deps, sets up the
venv + Playwright + Chromium, installs the systemd unit, enables & starts it.
Re-run any time without harm.

Before first run, make sure the host has a real `~/e-zapys/.env` (with secrets
filled in). The script does not touch env files.

## Releases (run from laptop)

```bash
bash deploy/sync.sh
```

`sync.sh` rsyncs the working tree (excluding `.env*`, `venv/`, `__pycache__/`),
refreshes Python deps if `requirements.txt` changed, and restarts the service.

To target a different host: `E_ZAPYS_HOST=other-host bash deploy/sync.sh`.

## Operations

```bash
# live logs
ssh instance-for-mia-centers-bot 'sudo journalctl -u e-zapys -f'

# status incl. memory / restart count
ssh instance-for-mia-centers-bot 'sudo systemctl status e-zapys'

# stop / start / restart
ssh instance-for-mia-centers-bot 'sudo systemctl restart e-zapys'
```

## Switching language

The bot reads its config from `$ENV_FILE` (default `.env`). To run an
English-language instance instead:

```bash
ssh instance-for-mia-centers-bot
cp ~/e-zapys/.env.en ~/e-zapys/.env
sudo systemctl restart e-zapys
```

To run **both** EN and UK simultaneously, copy the unit file twice with
different `ENV_FILE=` paths and `Description=`, install as
`e-zapys-uk.service` / `e-zapys-en.service`, and `systemctl enable --now`
each. (Each language needs its own `BOT_TOKEN` since one Telegram bot can't
have two `getUpdates` consumers.)

## Memory tuning

The unit caps memory at `MemoryHigh=600M` / `MemoryMax=750M`. If you see
`Failed with result 'oom-kill'` in `journalctl -u e-zapys` repeatedly, either:

- raise the caps in `deploy/e-zapys.service` and re-run `sync.sh`, or
- find the leak in the bot (long-lived Playwright contexts are the usual
  suspect — recycle the browser every N iterations).

Don't raise `MemoryMax` past ~800M without also bumping the EC2 instance —
914 MiB total RAM minus the kernel/sshd/etc. only leaves ~700 MiB for the bot.
