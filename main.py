from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me stats of two teams and I’ll predict the match outcome.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Simple dummy logic for now
    await update.message.reply_text("Prediction: Team A will win or it’ll be over 2.5 goals (sample response).")

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("predict", predict))

if __name__ == "__main__":
    app.run_polling()
