# Telegram Football Prediction Bot

A 24/7 Telegram bot hosted on Render that predicts football match outcomes.

## Features
- Match Winner
- Over/Under 2.5 Goals
- Both Teams to Score
- UptimeRobot-ready with Flask keep-alive route

## How to Deploy

### 1. Upload to GitHub

Push the code to a new GitHub repo.

### 2. Deploy on Render

- Go to [https://render.com](https://render.com)
- Click **"New Web Service"**
- Connect to your GitHub repo
- Use **Start Command**: `python main.py`
- Set Environment Variable:
  - `BOT_TOKEN = your telegram bot token`

### 3. Prevent Sleeping with UptimeRobot

- Visit [https://uptimerobot.com](https://uptimerobot.com)
- Add new HTTP monitor
- Use your Render URL (e.g., `https://your-bot.onrender.com`)
- Set interval to 5 minutes

Done — your bot runs 24/7!
