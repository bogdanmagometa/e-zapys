## E-zapys

**Problem.** Registering for a driving exam in Ukraine through the official [e-zapys](https://hsc.gov.ua/e-zapis/) portal requires constant manual checking for available time slots. Service centers of the Ministry of Internal Affairs (MIA) are extremely busy, and appointments get taken within minutes (sometimes seconds) of becoming available.

**Solution.** Automated monitoring with instant notifications. This bot continuously checks the e-zapys portal for appointment availability and sends a Telegram notification the moment a slot opens at your selected service centers. Subscribe to the centers you're interested in and get alerted immediately when they have availability.

This repo implements the solution.

Stack:
- Telegram bot for notifications
- Playwright for scraping and browser automation

## Deploy

### Setup environment

```
sudo apt update -y
sudo apt install -y python3 python3-venv xvfb

cd e-zapys

python3 -m venv venv

source venv/bin/activate

pip install pip --upgrade
pip install -r requirements.txt

playwright install-deps
playwright install
```

### Set environment vars

```
cp .env.example .env
```

Then modify `.env` with your secrets and setting.

### Launch

```
xvfb-run -a python3 main.py
```

## Access

Instances of the bot are deployed:
- Ukrainian version: Todo
- English version: https://t.me/mia_en_bot
