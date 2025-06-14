import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import os
from dotenv import load_dotenv

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Conversation states
(
    TEAM_NAMES,
    LEAGUE_STATUS,
    AVG_GOALS,
    HEAD_TO_HEAD,
    FORM,
    PREDICT,
) = range(6)

# Store user data
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Let's start a match prediction.\n\nWhat are the names of the two teams? (e.g., Team A vs Team B)")
    return TEAM_NAMES

async def get_team_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id] = {"teams": update.message.text}
    await update.message.reply_text("What is the league status of both teams? (e.g., Team A: 1st, Team B: 5th)")
    return LEAGUE_STATUS

async def get_league_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["league"] = update.message.text
    await update.message.reply_text("What is the average number of goals scored/conceded? (e.g., Team A: 1.5/1.0, Team B: 1.2/1.3)")
    return AVG_GOALS

async def get_avg_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["avg_goals"] = update.message.text
    await update.message.reply_text("What is the head-to-head record? (e.g., Team A won 3, Team B won 1, 2 draws)")
    return HEAD_TO_HEAD

async def get_head_to_head(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["h2h"] = update.message.text
    await update.message.reply_text("What is the recent form of both teams? (e.g., Team A: WWLDW, Team B: LLWDD)")
    return FORM

async def get_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["form"] = update.message.text

    data = user_data_store[update.effective_user.id]
    prediction = make_prediction(data)

    await update.message.reply_text(f"✅ Prediction Complete:\n\n{prediction}")
    return ConversationHandler.END

def make_prediction(data):
    # This is placeholder logic — you can customize it
    result = (
        f"Teams: {data['teams']}\n"
        f"League Status: {data['league']}\n"
        f"Avg Goals: {data['avg_goals']}\n"
        f"Head-to-Head: {data['h2h']}\n"
        f"Form: {data['form']}\n\n"
        f"🔮 Based on this info, it's likely to be a tight match. Slight edge to the better-form team."
    )
    return result

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prediction canceled.")
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN is not set in environment variables")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEAM_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_team_names)],
            LEAGUE_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_league_status)],
            AVG_GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_avg_goals)],
            HEAD_TO_HEAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_head_to_head)],
            FORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_form)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
