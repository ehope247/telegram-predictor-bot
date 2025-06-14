import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --- State Definitions for Conversation ---
TEAM_A, TEAM_B, AVG_GOAL_A, AVG_CONCEDE_A, FORM_A, \
AVG_GOAL_B, AVG_CONCEDE_B, FORM_B, H2H, PREDICT = range(10)

# --- Prediction Logic ---
def get_prediction(stats):
    """
    A simple prediction algorithm based on provided stats.
    This is a basic model and can be improved significantly.
    """
    # Assign weights to different factors
    weights = {
        'avg_goal': 1.5,
        'avg_concede': -1.0,
        'form': 2.0,
        'h2h': 1.2
    }

    # Calculate score for Team A
    score_a = (float(stats['avg_goal_a']) * weights['avg_goal'] +
               float(stats['avg_concede_a']) * weights['avg_concede'] +
               int(stats['form_a']) * weights['form'] +
               int(stats['h2h'].split('-')[0]) * weights['h2h'])

    # Calculate score for Team B
    score_b = (float(stats['avg_goal_b']) * weights['avg_goal'] +
               float(stats['avg_concede_b']) * weights['avg_concede'] +
               int(stats['form_b']) * weights['form'] +
               int(stats['h2h'].split('-')[1]) * weights['h2h'])

    # Determine the outcome
    if score_a > score_b + 2:
        return f"{stats['team_a']} is likely to win."
    elif score_b > score_a + 2:
        return f"{stats['team_b']} is likely to win."
    else:
        return "The match is likely to be a draw."

# --- Bot Command and Conversation Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the first team's name."""
    await update.message.reply_text(
        "Hi! I'm your match prediction bot.\n\n"
        "Let's start with the home team. What is the name of the first team?"
    )
    return TEAM_A

async def team_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the first team's name and asks for the second."""
    context.user_data['team_a'] = update.message.text
    await update.message.reply_text(
        f"Great! Team 1 is {context.user_data['team_a']}. "
        "Now, what is the name of the second team (away team)?"
    )
    return TEAM_B

async def team_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the second team's name and asks for the first team's avg goals."""
    context.user_data['team_b'] = update.message.text
    await update.message.reply_text(
        f"Understood. Now, what is {context.user_data['team_a']}'s average goals scored per match?"
    )
    return AVG_GOAL_A
    
# ... (Add functions for avg_goal_a, avg_concede_a, form_a)
async def avg_goal_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['avg_goal_a'] = update.message.text
    await update.message.reply_text(f"What is {context.user_data['team_a']}'s average goals conceded per match?")
    return AVG_CONCEDE_A

async def avg_concede_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['avg_concede_a'] = update.message.text
    await update.message.reply_text(f"How many of the last 5 matches did {context.user_data['team_a']} win? (Enter a number from 0 to 5)")
    return FORM_A

async def form_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['form_a'] = update.message.text
    await update.message.reply_text(f"Now for {context.user_data['team_b']}. What is their average goals scored per match?")
    return AVG_GOAL_B

# ... (Add functions for avg_goal_b, avg_concede_b, form_b)
async def avg_goal_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['avg_goal_b'] = update.message.text
    await update.message.reply_text(f"What is {context.user_data['team_b']}'s average goals conceded per match?")
    return AVG_CONCEDE_B

async def avg_concede_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['avg_concede_b'] = update.message.text
    await update.message.reply_text(f"How many of the last 5 matches did {context.user_data['team_b']} win? (Enter a number from 0 to 5)")
    return FORM_B

async def form_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['form_b'] = update.message.text
    await update.message.reply_text(f"Finally, what is the Head-to-Head record from the last 5 matches? "
                                    f"(e.g., if {context.user_data['team_a']} won 3 and {context.user_data['team_b']} won 2, enter '3-2')")
    return H2H


async def h2h_and_predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores H2H, runs prediction, and shows the result."""
    context.user_data['h2h'] = update.message.text
    
    # Get the prediction
    prediction_result = get_prediction(context.user_data)
    
    await update.message.reply_text(
        f"Calculating...\n\nHere is your prediction:\n{prediction_result}",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    # Clear user data for the next prediction
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Prediction cancelled. Type /start to begin again.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # It's recommended to get the token from environment variables for security
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("Please set the TELEGRAM_TOKEN environment variable.")

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

    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()
