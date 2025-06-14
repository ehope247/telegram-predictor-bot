import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

TEAM1, TEAM2, LEAGUE, GOALS, H2H, FORM = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Football Predictor Bot! ⚽\n\nLet's begin.\n\nWhat is Team 1 name?")
    return TEAM1

async def team1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["team1"] = update.message.text
    await update.message.reply_text("What is Team 2 name?")
    return TEAM2

async def team2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["team2"] = update.message.text
    await update.message.reply_text("What is the league status? (e.g., Top of the league, Relegation battle)")
    return LEAGUE

async def league(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["league"] = update.message.text
    await update.message.reply_text("Average goals scored/conceded by each team?")
    return GOALS

async def goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goals"] = update.message.text
    await update.message.reply_text("Head-to-head performance? (e.g., Team1 won 3 of last 5)")
    return H2H

async def h2h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["h2h"] = update.message.text
    await update.message.reply_text("Recent form of both teams? (e.g., WWWLL vs LDDWW)")
    return FORM

async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["form"] = update.message.text

    # Now generate prediction (this is a dummy logic; you can improve it)
    team1 = context.user_data["team1"]
    team2 = context.user_data["team2"]
    league = context.user_data["league"]
    goals = context.user_data["goals"]
    h2h = context.user_data["h2h"]
    form = context.user_data["form"]

    prediction = f"""📊 Prediction Summary:

🏟️ Match: {team1} vs {team2}
📌 League Status: {league}
⚽ Avg Goals: {goals}
🤝 Head-to-Head: {h2h}
📈 Form: {form}

💡 Prediction: {team1 if 'W' in form[:3] else team2} might have an edge!
(This is a basic prediction. Improve logic as needed.)
"""
    await update.message.reply_text(prediction)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prediction cancelled.")
    return ConversationHandler.END

if __name__ == "__main__":
    TOKEN = os.getenv("Telegram_bot")  # Make sure the key name matches Render's environment variable
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEAM1: [MessageHandler(filters.TEXT & ~filters.COMMAND, team1)],
            TEAM2: [MessageHandler(filters.TEXT & ~filters.COMMAND, team2)],
            LEAGUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, league)],
            GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals)],
            H2H: [MessageHandler(filters.TEXT & ~filters.COMMAND, h2h)],
            FORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, form)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()
