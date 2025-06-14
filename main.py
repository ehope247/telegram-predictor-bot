import os
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --- State Definitions for Conversation ---
# These are the different steps in our conversation
TEAM_A, TEAM_B, AVG_GOAL_A, AVG_CONCEDE_A, FORM_A, \
AVG_GOAL_B, AVG_CONCEDE_B, FORM_B, H2H, PREDICT = range(10)

# --- Prediction Logic ---
def get_prediction(stats):
    """
    A simple prediction algorithm based on provided stats.
    This is a basic model and can be improved significantly with more advanced logic.
    """
    try:
        # Assign weights to different factors
        weights = {
            'avg_goal': 1.5,
            'avg_concede': -1.2, # Negative weight for goals conceded
            'form': 2.0,         # Strong weight for recent form
            'h2h': 1.2
        }
        
        h2h_a, h2h_b = map(int, stats['h2h'].split('-'))

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

        # Determine the outcome
        difference = score_a - score_b
        
        # More detailed predictions based on score difference
        prediction = f"--- Prediction for {stats['team_a']} vs {stats['team_b']} ---\n\n"
        
        if difference > 3:
            prediction += f"Outcome: Strong win for {stats['team_a']}."
            prediction += "\nMarket Suggestion: {team_a} to Win (1), Over 2.5 Goals."
        elif difference > 1:
            prediction += f"Outcome: {stats['team_a']} is likely to win."
            prediction += "\nMarket Suggestion: {team_a} to Win or Draw (1X)."
        elif difference < -3:
            prediction += f"Outcome: Strong win for {stats['team_b']}."
            prediction += "\nMarket Suggestion: {team_b} to Win (2), Over 2.5 Goals."
        elif difference < -1:
            prediction += f"Outcome: {stats['team_b']} is likely to win."
            prediction += "\nMarket Suggestion: {team_b} to Win or Draw (X2)."
        else:
            prediction += "Outcome: The match is likely to be a draw."
            prediction += "\nMarket Suggestion: Draw (X), Under 2.5 Goals."
            
        return prediction.format(team_a=stats['team_a'], team_b=stats['team_b'])

    except Exception as e:
        print(f"Error during prediction: {e}")
        return "Sorry, an error occurred during calculation. Please check your inputs and try again."


# --- Bot Command and Conversation Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the first team's name."""
    await update.message.reply_text(
        "Hi! I'm your match prediction bot.\n\n"
        "Send /cancel at any time to stop.\n\n"
        "Let's start with the home team. What is the name of the first team?"
    )
    return TEAM_A

async def team_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team_a'] = update.message.text
    await update.message.reply_text(
        f"Great! Home team is {context.user_data['team_a']}.\n"
        "Now, what is the name of the away team?"
    )
    return TEAM_B

async def team_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['team_b'] = update.message.text
    await update.message.reply_text(
        f"Understood. Now, what is {context.user_data['team_a']}'s average goals scored per match? (e.g., 1.8)"
    )
    return AVG_GOAL_A

async def avg_goal_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        # Validate input is a number
        float(update.message.text)
        context.user_data['avg_goal_a'] = update.message.text
        await update.message.reply_text(f"And what is {context.user_data['team_a']}'s average goals conceded per match? (e.g., 0.9)")
        return AVG_CONCEDE_A
    except ValueError:
        await update.message.reply_text("That doesn't look like a number. Please enter the average goals scored (e.g., 1.8).")
        return AVG_GOAL_A

async def avg_concede_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        float(update.message.text)
        context.user_data['avg_concede_a'] = update.message.text
        await update.message.reply_text(f"How many of the last 5 matches did {context.user_data['team_a']} win? (Enter a number from 0 to 5)")
        return FORM_A
    except ValueError:
        await update.message.reply_text("That doesn't look like a number. Please enter the average goals conceded (e.g., 0.9).")
        return AVG_CONCEDE_A

async def form_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        form = int(update.message.text)
        if not 0 <= form <= 5:
            raise ValueError()
        context.user_data['form_a'] = update.message.text
        await update.message.reply_text(f"Got it. Now for {context.user_data['team_b']}.\nWhat is their average goals scored per match?")
        return AVG_GOAL_B
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid input. Please enter a whole number between 0 and 5.")
        return FORM_A

async def avg_goal_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        float(update.message.text)
        context.user_data['avg_goal_b'] = update.message.text
        await update.message.reply_text(f"And what is {context.user_data['team_b']}'s average goals conceded per match?")
        return AVG_CONCEDE_B
    except ValueError:
        await update.message.reply_text("That doesn't look like a number. Please enter the average goals scored.")
        return AVG_GOAL_B

async def avg_concede_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        float(update.message.text)
        context.user_data['avg_concede_b'] = update.message.text
        await update.message.reply_text(f"How many of the last 5 matches did {context.user_data['team_b']} win? (Enter a number from 0 to 5)")
        return FORM_B
    except ValueError:
        await update.message.reply_text("That doesn't look like a number. Please enter the average goals conceded.")
        return AVG_CONCEDE_B

async def form_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        form = int(update.message.text)
        if not 0 <= form <= 5:
            raise ValueError()
        context.user_data['form_b'] = update.message.text
        await update.message.reply_text(f"Finally, what is the Head-to-Head record from their last 5 encounters?\n"
                                        f"Use the format: ({context.user_data['team_a']} wins - {context.user_data['team_b']} wins). For example: 3-2")
        return H2H
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid input. Please enter a whole number between 0 and 5.")
        return FORM_B

async def h2h_and_predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores H2H, runs prediction, and shows the result."""
    h2h_input = update.message.text
    try:
        # Validate H2H format
        parts = h2h_input.split('-')
        if len(parts) != 2: raise ValueError()
        int(parts[0])
        int(parts[1])
        context.user_data['h2h'] = h2h_input
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid format. Please use the format '3-2' for Head-to-Head wins.")
        return H2H

    await update.message.reply_text("All data collected. Calculating prediction...", reply_markup=ReplyKeyboardRemove())
    
    # Get the prediction
    prediction_result = get_prediction(context.user_data)
    
    await update.message.reply_text(prediction_result)
    
    # Clear user data for the next prediction
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Prediction cancelled. Type /start to begin again.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("Please set the TELEGRAM_TOKEN environment variable on Render.")

    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states
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

    # Start the Bot. `drop_pending_updates=True` tells the bot to ignore old messages
    # that were sent while it was offline, preventing the weird startup behavior.
    print("Bot is starting...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
