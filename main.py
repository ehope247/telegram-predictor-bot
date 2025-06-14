import os
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging to see errors and bot activity
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- State Definitions for Conversation ---
TEAM_A, TEAM_B, AVG_GOAL_A, AVG_CONCEDE_A, FORM_A, \
AVG_GOAL_B, AVG_CONCEDE_B, FORM_B, H2H = range(9)

# --- Prediction Logic ---
def get_prediction(stats: dict) -> str:
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

# --- Bot Command and Conversation Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! I'm your match prediction bot.\n\n"
        "Send /cancel at any time to stop.\n\n"
        "Let's start with the home team. What is the name of the first team?"
    )
    return TEAM_A

async def team_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team_a'] = update.message.text
    await update.message.reply_text(f"Great! Home team is {context.user_data['team_a']}. Now, what is the name of the away team?")
    return TEAM_B

async def team_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team_b'] = update.message.text
    await update.message.reply_text(f"Understood. Now, what is {context.user_data['team_a']}'s average goals scored per match? (e.g., 1.8)")
    return AVG_GOAL_A

async def avg_goal_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_goal_a'] = str(float(update.message.text))
        await update.message.reply_text(f"And what is {context.user_data['team_a']}'s average goals conceded per match? (e.g., 0.9)")
        return AVG_CONCEDE_A
    except ValueError:
        await update.message.reply_text("That's not a valid number. Please enter average goals scored.")
        return AVG_GOAL_A

async def avg_concede_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_concede_a'] = str(float(update.message.text))
        await update.message.reply_text(f"How many of the last 5 matches did {context.user_data['team_a']} win? (Enter a number from 0 to 5)")
        return FORM_A
    except ValueError:
        await update.message.reply_text("That's not a valid number. Please enter average goals conceded.")
        return AVG_CONCEDE_A

async def form_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        form = int(update.message.text)
        if not 0 <= form <= 5: raise ValueError()
        context.user_data['form_a'] = str(form)
        await update.message.reply_text(f"Got it. Now for {context.user_data['team_b']}. What is their average goals scored per match?")
        return AVG_GOAL_B
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a whole number between 0 and 5.")
        return FORM_A

async def avg_goal_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_goal_b'] = str(float(update.message.text))
        await update.message.reply_text(f"And what is {context.user_data['team_b']}'s average goals conceded per match?")
        return AVG_CONCEDE_B
    except ValueError:
        await update.message.reply_text("That's not a valid number. Please enter average goals scored.")
        return AVG_GOAL_B

async def avg_concede_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['avg_concede_b'] = str(float(update.message.text))
        await update.message.reply_text(f"How many of the last 5 matches did {context.user_data['team_b']} win? (Enter a number from 0 to 5)")
        return FORM_B
    except ValueError:
        await update.message.reply_text("That's not a valid number. Please enter average goals conceded.")
        return AVG_CONCEDE_B

async def form_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        form = int(update.message.text)
        if not 0 <= form <= 5: raise ValueError()
        context.user_data['form_b'] = str(form)
        await update.message.reply_text(f"Finally, what is the Head-to-Head record from their last 5 encounters?\nUse the format: ({context.user_data['team_a']} wins - {context.user_data['team_b']} wins). For example: 3-2")
        return H2H
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a whole number between 0 and 5.")
        return FORM_B

async def h2h_and_predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        h2h_input = update.message.text
        parts = h2h_input.split('-')
        if len(parts) != 2 or not parts[0].strip().isdigit() or not parts[1].strip().isdigit(): raise ValueError()
        context.user_data['h2h'] = h2h_input
        
        await update.message.reply_text("All data collected. Calculating prediction...", reply_markup=ReplyKeyboardRemove())
        prediction_result = get_prediction(context.user_data)
        await update.message.reply_text(prediction_result)
        
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Invalid format. Please use the format '3-2' for Head-to-Head wins.")
        return H2H

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Prediction cancelled. Type /start to begin again.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.critical("CRITICAL: TELEGRAM_TOKEN environment variable not found.")
        raise ValueError("Please set the TELEGRAM_TOKEN environment variable on Render.")

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
    logger.info("Bot is starting and polling for updates...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
