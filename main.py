import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Store basic user state
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send teams like this:\n\nManchester United vs Liverpool")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if " vs " in text:
        user_state[update.effective_chat.id] = {"teams": text}
        await update.message.reply_text("Are they in the same league? (yes or no)")
    elif text in ["yes", "no"] and update.effective_chat.id in user_state:
        user_state[update.effective_chat.id]["same_league"] = text
        await update.message.reply_text(
            "Now send team stats like this:\n\n"
            "Team A:\nTable 2\nAvg goal 2.1\nAvg conceded 1.0\nHead to head win 2 lose 1 draw 1\nForm WWDDL\n\n"
            "Team B:\nTable 5\nAvg goal 1.6\nAvg conceded 1.3\nForm WLDDL"
        )
    else:
        await update.message.reply_text("🔮 Prediction: Based on these stats, Team A may have an edge.\n(More logic coming soon)")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    app.run_polling()
