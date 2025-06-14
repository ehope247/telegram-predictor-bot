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
# These are the different steps in our conversation
TEAM_A, TEAM_B, AVG_GOAL_A, AVG_CONCEDE_A, FORM_A, \
AVG_GOAL_B, AVG_CONCEDE_B, FORM_B, H2H = range(9)

# --- Prediction Logic ---
def get_prediction(stats: dict) -> str:
    """
    A simple prediction algorithm based on provided stats.
    This now includes suggestions for other markets.
    """
    try:
        # Assign weights to different factors
        weights = {
            'avg_goal': 1.5,
            'avg_concede': -1.3, # Negative weight for goals conceded
            'form': 2.0,         # Strong weight for recent form
            'h2h': 1.2
        }

        h2h_a, h2h_b = map(int, stats['h2h'].split('-'))
        total_goals_scored = float(stats['avg_goal_a']) + float(stats['avg_goal_b'])
        total_goals_conceded = float(stats['avg_concede_a']) + float(stats['avg_concede_b'])

        # Calculate score for Team A
        score_a = (float(stats['avg_goal_a']) * weights['avg_goal'] +
                   float(stats['avg_concede_a']) * weights['avg_concede'] +
                   int(stats['form_a']) * weights['form'] +
                   h2h_a * weights['h2h'])

        # Calculate score for Team B
        score_b = (float(stats['avg_goal_b']) * weights['avg_goal'] +
                   float(stats['avg_concede_b']) * weights['avg_concede'] +
                   int(stats['form_b']) * weights['form'] +
                   h2h_b * weights['h2h'])

        # --- Generate Prediction Text ---
        prediction = f"--- Prediction for {stats['team_a']} vs {stats['team_b']} ---\n\n"
        difference = score_a - score_b

        # Main Outcome Prediction
        if difference > 2.5:
            prediction += f"🏆 Main Outcome: Strong win for {stats['team_a']}.\n"
        elif difference > 0.5:
            prediction += f"🏆 Main Outcome: {stats['team_a']} has a slight advantage.\n"
        elif difference < -2.5:
            prediction += f"🏆 Main Outcome: Strong win for {stats['team_b']}.\n"
        elif difference < -0.5:
            prediction += f"🏆 Main Outcome: {stats['team_b']} has a slight advantage.\n"
        else:
            prediction += "🏆 Main Outcome: The match is likely to be a draw.\n"

        # Goals Market Prediction
        if total_goals_scored > 3.0 or total_goals_conceded > 3.0:
            prediction += "⚽ Goals Market: Likely Over 2.5 goals.\n"
        elif total_goals_scored < 2.2 and total_goals_conceded < 2.2:
             prediction += "⚽ Goals Market: Likely Under 2.5 goals.\n"
        else:
             prediction += "⚽ Goals Market: Unclear, could go either way.\n"

        # Both Teams to Score (BTTS) Prediction
        if float(stats['avg_goal_a']) > 1 and float(stats['avg_goal_b']) > 1 and float(stats['avg_concede_a']) > 0.8 and float(stats['avg_concede_b']) > 0.8:
            prediction += "🥅 Both Teams to Score: Yes (GG).\n"
        else:
            prediction += "🥅 Both Teams to Score: No (NG).\n"

        return prediction

    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        return "Sorry, an error occurred during calculation. Please check your inputs by typing /start again."

# --- Bot Command and Conversation Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! I'm your match prediction bot.\n\n"
        "I will ask you for 8 pieces of information to make a prediction.\n"
        "Send /cancel at any time to stop.\n\n"
        "Let's start with the home team. What is the name of the first team?"
    )
    return TEAM_A

async def get_text_input(state_key: str, next_state: int, prompt: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data[state_key] = update.message.text
        team_a = context.user_data.get('team_a', 'Team A')
        team_b = context.user_data.get('team_b', 'Team B')
        await update.message.reply_text(prompt.format(team_a=team_a, team_b=team_b))
        return next_state
    return handler

async def get_numerical_input(state_key: str, next_state: int, prompt: str, validation_error: str, is_int: bool = False, min_val=None, max_val=None):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            value = int(update.message.text) if is_int else float(update.message.text)
            if (min_val is not None and value < min_val) or \
               (max_val is not None and value > max_val):
                raise ValueError()
            context.user_data[state_key] = str(value)
            team_a = context.user_data.get('team_a', 'Team A')
            team_b = context.user_data.get('team_b', 'Team B')
            await update.message.reply_text(prompt.format(team_a=team_a, team_b=team_b))
            return next_state
        except (ValueError, TypeError):
            await update.message.reply_text(validation_error)
            return await handler(update, context)
    return handler

async def h2h_and_predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    h2h_input = update.message.text
    try:
        parts = h2h_input.split('-')
        if len(parts) != 2 or not parts[0].strip().isdigit() or not parts[1].strip().isdigit():
            raise ValueError()
        context.user_data['h2h'] = h2h_input
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid format. Please use the format '3-2' for Head-to-Head wins.")
        return H2H

    await update.message.reply_text("All data collected. Calculating prediction...", reply_markup=ReplyKeyboardRemove())
    prediction_result = get_prediction(context.user_data)
    await update.message.reply_text(prediction_result)
    context.user_data.clear()
    return ConversationHandler.END

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
            TEAM_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_text_input('team_a', TEAM_B, "Great! Home team is {team_a}. Now, what is the name of the away team?"))],
            TEAM_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_text_input('team_b', AVG_GOAL_A, "Understood. Now, what is {team_a}'s average goals scored per match? (e.g., 1.8)"))],
            AVG_GOAL_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_numerical_input('avg_goal_a', AVG_CONCEDE_A, "And what is {team_a}'s average goals conceded per match? (e.g., 0.9)", "That's not a valid number. Please enter average goals scored."))],
            AVG_CONCEDE_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_numerical_input('avg_concede_a', FORM_A, "How many of the last 5 matches did {team_a} win? (Enter a number from 0 to 5)", "That's not a valid number. Please enter average goals conceded."))],
            FORM_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_numerical_input('form_a', AVG_GOAL_B, "Got it. Now for {team_b}. What is their average goals scored per match?", "Invalid input. Please enter a whole number between 0 and 5.", is_int=True, min_val=0, max_val=5))],
            AVG_GOAL_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_numerical_input('avg_goal_b', AVG_CONCEDE_B, "And what is {team_b}'s average goals conceded per match?", "That's not a valid number. Please enter average goals scored."))],
            AVG_CONCEDE_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_numerical_input('avg_concede_b', FORM_B, "How many of the last 5 matches did {team_b} win? (Enter a number from 0 to 5)", "That's not a valid number. Please enter average goals conceded."))],
            FORM_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_numerical_input('form_b', H2H, "Finally, what is the Head-to-Head record from their last 5 encounters?\nUse the format: ({team_a} wins - {team_b} wins). For example: 3-2", "Invalid input. Please enter a whole number between 0 and 5.", is_int=True, min_val=0, max_val=5))],
            H2H: [MessageHandler(filters.TEXT & ~filters.COMMAND, h2h_and_predict)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    logger.info("Bot is starting and polling for updates...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
