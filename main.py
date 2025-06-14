import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

import os
from flask import Flask

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Telegram bot token from environment
TOKEN = os.environ.get("BOT_TOKEN")

# Flask server for keeping bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Conversation states
(
    TEAM_NAMES,
    GOALS_SCORED,
    GOALS_CONCEDED,
    LAST_5_FORM,
    H2H_RESULTS,
) = range(5)

user_data = {}

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Let's start predicting a match.\nWhat are the team names? (Home vs Away)")
    return TEAM_NAMES

async def team_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["team_names"] = update.message.text
    await update.message.reply_text("Enter average goals scored (Home, Away):")
    return GOALS_SCORED

async def goals_scored(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["goals_scored"] = update.message.text
    await update.message.reply_text("Enter average goals conceded (Home, Away):")
    return GOALS_CONCEDED

async def goals_conceded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["goals_conceded"] = update.message.text
    await update.message.reply_text("Enter last 5 match form (Home wins, Away wins):")
    return LAST_5_FORM

async def last_5_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["last_5_form"] = update.message.text
    await update.message.reply_text("Enter H2H results summary (e.g., Home 3W - Away 2W):")
    return H2H_RESULTS

async def h2h_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["h2h"] = update.message.text
    # Do fake prediction for now (you can add logic here)
    prediction = "🔮 Prediction:\n"
    prediction += f"🏆 Match Result: Possibly {user_data['team_names'].split(' vs ')[0]} to win or Draw.\n"
    prediction += f"⚽ Over/Under 2.5 Goals: Over 2.5 Goals.\n"
    prediction += f"🤝 Both Teams to Score: Yes."
    await update.message.reply_text(prediction)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

def main():
    app_bot = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TEAM_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, team_names)],
            GOALS_SCORED: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals_scored)],
            GOALS_CONCEDED: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals_conceded)],
            LAST_5_FORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_5_form)],
            H2H_RESULTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h2h_results)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app_bot.add_handler(conv_handler)
    print("✅ Bot is alive!")

    # Start the bot
    app_bot.run_polling()

if __name__ == '__main__':
    from threading import Thread
    Thread(target=main).start()
    app.run(host="0.0.0.0", port=10000)
