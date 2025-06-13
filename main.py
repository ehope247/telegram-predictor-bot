import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me 'Team A vs Team B' to predict the winner.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a message like 'Arsenal vs Chelsea' to get a prediction.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    if " vs " in message.lower():
        team1, team2 = message.split(" vs ")
        team1 = team1.strip().title()
        team2 = team2.strip().title()
        # This is a placeholder; you can improve this later
        prediction = f"🔮 Prediction:\n{team1} vs {team2}\nWinner: {team1} (for example)"
        await update.message.reply_text(prediction)
    else:
        await update.message.reply_text("Please send in format like: Arsenal vs Chelsea")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, predict))

    print("✅ Bot is running...")
    app.run_polling()
