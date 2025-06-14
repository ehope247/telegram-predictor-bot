import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --- Standard Setup: Logging ---
# This helps us see what the bot is doing in the Render logs.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- The Flask Web Server ---
# This part is ESSENTIAL for Render's Free Web Service.
# It opens a "port" to listen for web traffic, which Render needs to see.
# Its only job is to respond "I'm alive!" when UptimeRobot visits.
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Bot is alive and polling!'


# --- Your Bot's Logic and Functions ---

# State Definitions for the conversation
TEAM_A, TEAM_B, AVG_GOAL_A, AVG_CONCEDE_A, FORM_A, \
AVG_GOAL_B, AVG_CONCEDE_B, FORM_B, H2H = range(9)

def get_prediction(stats: dict) -> str:
    """Calculates the match prediction based on user-provided stats."""
    try:
        weights = {'avg_goal': 1.5, 'avg_concede': -1.3, 'form': 2.0, 'h2h': 1.2}
        h2h_a, h2h_b = map(int, stats['h2h'].split('-'))
        total_goals_scored = float(stats['avg_goal_a']) + float(stats['avg_goal_b'])
        total_goals_conceded = float(stats['avg_concede_a']) + float(stats['avg_concede_b'])
        score_a = (float(stats['avg_goal_a']) * weights['avg_goal'] + float(stats['avg_concede_a']) * weights['avg_concede'] + int(stats['form_a']) * weights['form'] + h2h_a * weights['h2h'])
        score_b = (float(stats['avg_goal_b']) * weights['avg_goal'] + float(stats['avg_concede_b']) * weights['avg_concede'] + int(stats['form_b']) * weights['form'] + h2h_b * weights['h2h'])
        
        prediction = f"--- Prediction for {stats['team_a']} vs {stats['team_b']} ---\n\n"
        difference = score_a - score_b

        if difference > 2.5: prediction += f"🏆 Main Outcome: Strong win for {stats['team_a']}.\n"
        elif difference > 0.5: prediction += f"🏆 Main Outcome: {stats['team_a']} has a slight advantage.\n"
        elif difference < -2.5: prediction += f"🏆 Main Outcome: Strong win for {stats['team_b']}.\n"
        elif difference < -0.5: prediction += f"🏆 Main Outcome: {stats['team_b']} has a slight advantage.\n"
        else: prediction += "🏆 Main Outcome: The match is likely to be a draw.\n"

        if total_goals_scored > 3.0 or total_goals_conceded > 3.0: prediction += "⚽ Goals Market: Likely Over 2.5 goals.\n"
        elif total_goals_scored < 2.2 and total_goals_conceded < 2.2: prediction += "⚽ Goals Market: Likely Under 2.5 goals.\n"
        else: prediction += "⚽ Goals Market: Unclear, could go either way.\n"
        
        if float(stats['avg_goal_a']) > 1 and float(stats['avg_goal_b']) > 1 and float(stats['avg_concede_a']) > 0.8 and float(stats['avg_concede_b']) > 0.8: prediction += "🥅 Both Teams to Score: Yes (GG).\n"
        else: prediction += "🥅 Both Teams to Score: No (NG).\n"
        
        return prediction
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        return "Sorry, an error occurred during calculation. Please /start again."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Hi! I'm your match prediction bot.\n\nSend /cancel to stop.\n\nWhat is the name of the home team?")
    return TEAM_A
async def team_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team_a'] = update.message.text
    await update.message.reply_text(f"Home team is {context.user_data['team_a']}. Now, the away team?")
    return TEAM_B
async def team_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team_b'] = update.message.text
    await update.message.reply_text(f"{context.user_data['team_a']}'s average goals scored?")
    return AVG_GOAL_A
async def avg_goal_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_goal_a'] = str(float(update.message.text))
        await update.message.reply_text(f"{context.user_data['team_a']}'s average goals conceded?")
        return AVG_CONCEDE_A
    except ValueError:
        await update.message.reply_text("Invalid number. Try again.")
        return AVG_GOAL_A
async def avg_concede_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_concede_a'] = str(float(update.message.text))
        await update.message.reply_text(f"Wins in last 5 for {context.user_data['team_a']}? (0-5)")
        return FORM_A
    except ValueError:
        await update.message.reply_text("Invalid number. Try again.")
        return AVG_CONCEDE_A
async def form_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        form = int(update.message.text)
        if not 0 <= form <= 5: raise ValueError()
        context.user_data['form_a'] = str(form)
        await update.message.reply_text(f"Now for {context.user_data['team_b']}. Average goals scored?")
        return AVG_GOAL_B
    except ValueError:
        await update.message.reply_text("Invalid. Enter 0-5.")
        return FORM_A
async def avg_goal_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_goal_b'] = str(float(update.message.text))
        await update.message.reply_text(f"{context.user_data['team_b']}'s average goals conceded?")
        return AVG_CONCEDE_B
    except ValueError:
        await update.message.reply_text("Invalid number. Try again.")
        return AVG_GOAL_B
async def avg_concede_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_concede_b'] = str(float(update.message.text))
        await update.message.reply_text(f"Wins in last 5 for {context.user_data['team_b']}? (0-5)")
        return FORM_B
    except ValueError:
        await update.message.reply_text("Invalid number. Try again.")
        return AVG_CONCEDE_B
async def form_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        form = int(update.message.text)
        if not 0 <= form <= 5: raise ValueError()
        context.user_data['form_b'] = str(form)
        await update.message.reply_text(f"H2H record? ({context.user_data['team_a']} wins - {context.user_data['team_b']} wins). E.g., 3-2")
        return H2H
    except ValueError:
        await update.message.reply_text("Invalid. Enter 0-5.")
        return FORM_B
async def h2h_and_predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        h2h_input = update.message.text
        parts = h2h_input.split('-')
        if len(parts) != 2 or not parts[0].strip().isdigit() or not parts[1].strip().isdigit(): raise ValueError()
        context.user_data['h2h'] = h2h_input
        await update.message.reply_text("Calculating...", reply_markup=ReplyKeyboardRemove())
        prediction_result = get_prediction(context.user_data)
        await update.message.reply_text(prediction_result)
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Invalid format. Use '3-2'.")
        return H2H
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def run_bot():
    """This function contains all the bot's logic and setup."""
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.critical("CRITICAL: TELEGRAM_TOKEN environment variable not found!")
        return # Stop the bot thread if the token is missing

    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEAM_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, team_a)],
            TEAM_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, team_b)],
            AVG_GOAL_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, avg_goal_a)],
            AVG_CONCEDE_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, avg_concede_a)],
            FORM_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, form_a)],
            AVG_GOAL_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, avg_goal_b)],
            AVG_CONCEDE_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, avg_concede_b)],
            FORM_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, form_b)],
            H2H: [MessageHandler(filters.TEXT & ~filters.COMMAND, h2h_and_predict)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    logger.info("Starting bot polling in background thread...")
    application.run_polling(drop_pending_updates=True)


# --- The Magic Part that Starts Everything ---
# This code runs AUTOMATICALLY when Render starts the web server.
# It creates and starts a new "thread" (a separate task) to run our bot.
# This allows the Web Server and the Bot to run at the same time.
logger.info("Setting up bot thread...")
bot_thread = threading.Thread(target=run_bot)
bot_thread.start()
