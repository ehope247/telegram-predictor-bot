import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

user_states = {}
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send team names like: Manchester United vs Liverpool")
    user_states[update.effective_user.id] = "awaiting_match"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    if user_id not in user_states:
        await update.message.reply_text("Please type /start to begin.")
        return

    state = user_states[user_id]

    if state == "awaiting_match":
        if " vs " in message.lower():
            user_data[user_id] = {"match": message}
            user_states[user_id] = "awaiting_league"
            await update.message.reply_text("Are these teams in the same league? (Yes/No)")
        else:
            await update.message.reply_text("Please use format: Team A vs Team B")

    elif state == "awaiting_league":
        if message.lower() in ["yes", "no"]:
            user_data[user_id]["same_league"] = message.lower()
            if message.lower() == "yes":
                user_states[user_id] = "awaiting_home_stats"
                await update.message.reply_text("Enter Home Team stats:\nFormat:\nTable 1\nAvg goal 2.1\nAvg conceder 1.1\nHead to head draw 1, win 2, lose 1\nLast five match LLDDE")
            else:
                user_states[user_id] = "awaiting_home_basic"
                await update.message.reply_text("Enter Home Team stats:\nFormat:\nAvg goal 2.1\nAvg conceder 1.1\nLast five match LLDDE")
        else:
            await update.message.reply_text("Please type Yes or No")

    elif state == "awaiting_home_stats":
        user_data[user_id]["home_stats"] = message
        user_states[user_id] = "awaiting_away_stats"
        await update.message.reply_text("Enter Away Team stats in same format.")

    elif state == "awaiting_home_basic":
        user_data[user_id]["home_stats"] = message
        user_states[user_id] = "awaiting_away_basic"
        await update.message.reply_text("Enter Away Team stats in same format.")

    elif state in ["awaiting_away_stats", "awaiting_away_basic"]:
        user_data[user_id]["away_stats"] = message
        user_states[user_id] = "done"
        await update.message.reply_text("Processing prediction...")

        # Placeholder prediction logic
        prediction = f"🏆 Likely winner: {user_data[user_id]['match'].split(' vs ')[0]}\n⚽ Over 2.5 Goals: YES\n🔮 Confidence: Medium"
        await update.message.reply_text(prediction)

        # Restarting
        user_states[user_id] = "awaiting_match"
        await update.message.reply_text("You can start again with a new match.")

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()