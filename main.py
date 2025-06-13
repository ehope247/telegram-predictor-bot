import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)

BOT_TOKEN = os.environ.get("Telegram_bot")

# Define conversation stages
MATCH_INPUT, SAME_LEAGUE, HOME_STATS, AWAY_STATS = range(4)

# Store user data during conversation
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Match Prediction Bot!\nSend the match like this:\n`Manchester United vs Liverpool`")
    return MATCH_INPUT

async def match_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["match"] = update.message.text
    await update.message.reply_text("Are both teams in the same league? (Yes/No)")
    return SAME_LEAGUE

async def same_league(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["same_league"] = update.message.text.lower()
    if user_data["same_league"] == "yes":
        await update.message.reply_text(
            "Send stats for the **home team** like this:\n"
            "`TeamName\nTable 1\nAvg goal 2.1\nAvg conceded 1.1\nHead to head draw 1, win 2, lose 1\nLast five match: LLDDE`"
        )
        return HOME_STATS
    else:
        await update.message.reply_text(
            "Send stats for the **home team** like this:\n"
            "`TeamName\nAvg goal 2.1\nAvg conceded 1.1\nLast five match: LLDDE`"
        )
        return HOME_STATS

async def home_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["home_stats"] = update.message.text
    await update.message.reply_text("Now send stats for the **away team** in the same format.")
    return AWAY_STATS

async def away_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["away_stats"] = update.message.text
    # Dummy prediction logic
    await update.message.reply_text("📊 Analyzing stats...")
    await update.message.reply_text(
        f"✅ Prediction for {user_data['match']}:\n"
        f"🏆 Likely Winner: Home Team\n"
        f"📈 Market Tips: Over 2.5 Goals, Both Teams to Score"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prediction canceled.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MATCH_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, match_input)],
            SAME_LEAGUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, same_league)],
            HOME_STATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, home_stats)],
            AWAY_STATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, away_stats)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
