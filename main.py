import os
import telegram
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters, Dispatcher
)

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()
dispatcher: Dispatcher = application.dispatcher

# States
TEAM_NAMES, GOALS_SCORED, GOALS_CONCEDED, LAST_5_FORM, H2H_RESULTS = range(5)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter team names (e.g. TeamA vs TeamB):")
    return TEAM_NAMES

async def team_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['teams'] = update.message.text
    await update.message.reply_text("Enter average goals scored per match (e.g. 1.5 vs 1.2):")
    return GOALS_SCORED

async def goals_scored(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['goals_scored'] = update.message.text
    await update.message.reply_text("Enter average goals conceded per match (e.g. 1.0 vs 0.9):")
    return GOALS_CONCEDED

async def goals_conceded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['goals_conceded'] = update.message.text
    await update.message.reply_text("Enter last 5 match form (e.g. 3 wins vs 2 wins):")
    return LAST_5_FORM

async def last_5_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['form'] = update.message.text
    await update.message.reply_text("Enter Head-to-Head result summary (e.g. 2 wins vs 1 win):")
    return H2H_RESULTS

async def h2h_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['h2h'] = update.message.text
    goals1 = list(map(float, user_data['goals_scored'].split("vs")))
    conceded1 = list(map(float, user_data['goals_conceded'].split("vs")))
    form_wins = list(map(int, user_data['form'].split("vs")))
    h2h_wins = list(map(int, user_data['h2h'].split("vs")))

    team1_chance = goals1[0] - conceded1[1] + form_wins[0] + h2h_wins[0]
    team2_chance = goals1[1] - conceded1[0] + form_wins[1] + h2h_wins[1]

    if team1_chance > team2_chance:
        result = "Prediction: Team 1 (Home) Win 🏆"
    elif team2_chance > team1_chance:
        result = "Prediction: Team 2 (Away) Win 🥇"
    else:
        result = "Prediction: Draw ⚖️"

    avg_total_goals = sum(goals1 + conceded1) / 2
    over_under = "Over 2.5 Goals 🔥" if avg_total_goals > 2.5 else "Under 2.5 Goals 🧊"
    both_score = "Both Teams to Score: YES 🔥" if goals1[0] > 0.8 and goals1[1] > 0.8 else "Both Teams to Score: NO ❌"

    final = f"""
*Match Prediction Results:*
{user_data['teams']}

{result}
{over_under}
{both_score}
"""
    await update.message.reply_text(final, parse_mode='Markdown')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prediction cancelled.")
    return ConversationHandler.END

# Telegram webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def home():
    return 'Bot is running!'

def setup():
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
    dispatcher.add_handler(conv_handler)

if __name__ == '__main__':
    setup()
    # Set webhook (only once or on each boot)
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/webhook"
    bot.setWebhook(url=webhook_url)

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
