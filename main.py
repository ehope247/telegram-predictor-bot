import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

TEAM1, TEAM2, STATS = range(3)
user_data_store = {}

@app.route('/')
def home():
    return "Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Welcome to Football Match Predictor Bot! Please enter the name of Team A.")

async def team1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team1'] = update.message.text
    await update.message.reply_text("Enter the name of Team 2:")
    return TEAM2

async def team2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team2'] = update.message.text
    await update.message.reply_text("Now enter match stats in this format:

"
                                    "avg_goals_team1, avg_goals_conceded_team1, form_team1 (WDLWW), "
                                    "avg_goals_team2, avg_goals_conceded_team2, form_team2 (DLLWW), "
                                    "H2H results (WDWLD)")
    return STATS

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['stats'] = update.message.text
    result = predict_outcome(context.user_data)
    await update.message.reply_text(result)
    return ConversationHandler.END

def predict_outcome(data):
    try:
        team1 = data['team1']
        team2 = data['team2']
        stats = data['stats'].split(',')
        g1, gc1, form1 = float(stats[0]), float(stats[1]), stats[2].strip()
        g2, gc2, form2 = float(stats[3]), float(stats[4]), stats[5].strip()
        h2h = stats[6].strip()

        score_team1 = g1 + (form1.count('W') * 0.5) + (h2h.count('W') * 0.3)
        score_team2 = g2 + (form2.count('W') * 0.5) + (h2h.count('L') * 0.3)

        outcome = "Draw"
        if score_team1 > score_team2 + 0.5:
            outcome = f"{team1} to Win"
        elif score_team2 > score_team1 + 0.5:
            outcome = f"{team2} to Win"

        over25 = "Over 2.5 Goals" if (g1 + g2) > 2.5 else "Under 2.5 Goals"
        btts = "Both Teams to Score: YES" if gc1 > 0.8 and gc2 > 0.8 else "Both Teams to Score: NO"

        return f"📊 Prediction for {team1} vs {team2}:

🏆 Outcome: {outcome}
🎯 {over25}
🤝 {btts}"
    except Exception as e:
        return f"⚠️ Error in prediction input: {str(e)}"

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Prediction cancelled.")
    return ConversationHandler.END

def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEAM1: [MessageHandler(filters.TEXT & ~filters.COMMAND, team1)],
            TEAM2: [MessageHandler(filters.TEXT & ~filters.COMMAND, team2)],
            STATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, stats)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
