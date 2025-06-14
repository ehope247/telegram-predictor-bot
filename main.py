from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import os

app = Flask(__name__)

TEAM_NAMES, GOALS_SCORED, GOALS_CONCEDED, LAST_5_FORM, H2H_RESULTS = range(5)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Let's predict a football match result.")
    await update.message.reply_text("Enter the team names (e.g. Arsenal vs Chelsea):")
    return TEAM_NAMES

async def team_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['teams'] = update.message.text
    await update.message.reply_text("Enter average goals scored per match (e.g. 1.8 vs 1.2):")
    return GOALS_SCORED

async def goals_scored(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['goals_scored'] = update.message.text
    await update.message.reply_text("Enter average goals conceded per match (e.g. 1.0 vs 1.5):")
    return GOALS_CONCEDED

async def goals_conceded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['goals_conceded'] = update.message.text
    await update.message.reply_text("Enter last 5 match form (e.g. 3 wins vs 2 wins):")
    return LAST_5_FORM

async def last_5_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['form'] = update.message.text
    await update.message.reply_text("Enter Head-to-Head results summary (e.g. Team A won 3, Team B won 2):")
    return H2H_RESULTS

async def h2h_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['h2h'] = update.message.text

    goals1, goals2 = map(float, user_data['goals_scored'].split("vs"))
    conceded1, conceded2 = map(float, user_data['goals_conceded'].split("vs"))
    team1_wins = int(user_data['form'].split("vs")[0].strip().split()[0])
    team2_wins = int(user_data['form'].split("vs")[1].strip().split()[0])

    team1_chance = goals1 - conceded2 + team1_wins
    team2_chance = goals2 - conceded1 + team2_wins

    if team1_chance > team2_chance:
        result = "Prediction: Team 1 (Home) Win 🏠"
    elif team2_chance > team1_chance:
        result = "Prediction: Team 2 (Away) Win 🛫"
    else:
        result = "Prediction: Draw ⚖️"

    avg_total_goals = (goals1 + goals2 + conceded1 + conceded2) / 2
    over_under = "Over 2.5 Goals ✅" if avg_total_goals > 2.5 else "Under 2.5 Goals ❌"
    both_teams_score = "Both Teams to Score: YES 🔥" if goals1 > 0.8 and goals2 > 0.8 else "Both Teams to Score: NO 🧊"

    prediction = f"""
📊 *Match Prediction Results*:
{user_data['teams']}

{result}
{over_under}
{both_teams_score}
    """

    await update.message.reply_text(prediction, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prediction cancelled.")
    return ConversationHandler.END

@app.route('/')
def home():
    return 'Bot is running!'

async def run_telegram_bot():
    TOKEN = os.environ.get("BOT_TOKEN")
    app_builder = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEAM_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, team_names)],
            GOALS_SCORED: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals_scored)],
            GOALS_CONCEDED: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals_conceded)],
            LAST_5_FORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_5_form)],
            H2H_RESULTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h2h_results)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app_builder.add_handler(conv_handler)
    await app_builder.initialize()
    await app_builder.start()
    await app_builder.updater.start_polling()
    await app_builder.updater.idle()

if __name__ == '__main__':
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    import asyncio
    asyncio.run(run_telegram_bot())
