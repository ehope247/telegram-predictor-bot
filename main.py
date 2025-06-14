import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# Conversation states
(TEAM_NAMES, GOALS_SCORED, GOALS_CONCEDED, FORM, H2H) = range(5)
user_data = {}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Telegram Conversation Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Let's predict a football match.\nEnter team names: Home vs Away")
    return TEAM_NAMES

async def team_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teams = update.message.text.split(" vs ")
    if len(teams) != 2:
        await update.message.reply_text("Use this format: Home vs Away")
        return TEAM_NAMES
    user_data[update.effective_chat.id] = {
        "home_team": teams[0].strip(),
        "away_team": teams[1].strip()
    }
    await update.message.reply_text(
        "Enter average goals scored per match (e.g., 1.5 vs 1.2):")
    return GOALS_SCORED

async def goals_scored(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        a, b = update.message.text.split(" vs ")
        user_data[update.effective_chat.id].update({
            "home_scored": float(a),
            "away_scored": float(b)
        })
        await update.message.reply_text(
            "Enter average goals conceded per match (e.g., 1.0 vs 1.4):")
        return GOALS_CONCEDED
    except:
        await update.message.reply_text("Invalid format. Use x.x vs y.y")
        return GOALS_SCORED

async def goals_conceded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        a, b = update.message.text.split(" vs ")
        user_data[update.effective_chat.id].update({
            "home_conceded": float(a),
            "away_conceded": float(b)
        })
        await update.message.reply_text("Enter last 5 match form (wins: e.g., 3 vs 2):")
        return FORM
    except:
        await update.message.reply_text("Invalid format. Use x vs y")
        return GOALS_CONCEDED

async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        a, b = update.message.text.split(" vs ")
        user_data[update.effective_chat.id].update({
            "home_form": int(a),
            "away_form": int(b)
        })
        await update.message.reply_text("Enter H2H summary (e.g., Home 2 wins, 1 draw, Away 2 wins):")
        return H2H
    except:
        await update.message.reply_text("Invalid format. Use numbers like x vs y")
        return FORM

async def h2h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data[update.effective_chat.id]
    data["h2h"] = update.message.text
    # Calculation
    total_home = data["home_scored"] + data["away_conceded"]
    total_away = data["away_scored"] + data["home_conceded"]
    avg_goals = (total_home + total_away) / 2
    # Predictions
    if data["home_form"] > data["away_form"] and total_home > total_away:
        result = f"{data['home_team']} Win"
    elif data["away_form"] > data["home_form"] and total_away > total_home:
        result = f"{data['away_team']} Win"
    else:
        result = "Draw"
    over_under = "Over 2.5 Goals" if avg_goals > 2.5 else "Under 2.5 Goals"
    btts = "Yes" if data["home_scored"] > 0.8 and data["away_scored"] > 0.8 else "No"
    message = (
        f"📊 Predictions:\n"
        f"🏆 Result: {result}\n"
        f"⚽ Over/Under 2.5: {over_under}\n"
        f"🤝 BTTS: {btts}\n"
        f"📚 H2H summary: {data['h2h']}"
    )
    await update.message.reply_text(message)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prediction cancelled!")
    return ConversationHandler.END

def run_telegram_bot():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEAM_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, team_names)],
            GOALS_SCORED: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals_scored)],
            GOALS_CONCEDED: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals_conceded)],
            FORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, form)],
            H2H: [MessageHandler(filters.TEXT & ~filters.COMMAND, h2h)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.run_polling()

# Flask server for UptimeRobot
flask_app = Flask(__name__)
@flask_app.route("/")
def home(): return "Bot is alive!"

if __name__ == "__main__":
    threading.Thread(target=run_telegram_bot).start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
