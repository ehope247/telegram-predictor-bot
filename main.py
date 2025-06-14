import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Get token from environment variable
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing. Set it in Render.")

# Conversation states
TEAM_NAMES, LEAGUE_STATUS, AVG_GOALS, HEAD_TO_HEAD, FORM = range(5)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Football Predictor Bot!\n\nPlease enter the **home team** and **away team** names (e.g., Arsenal vs Chelsea):")
    return TEAM_NAMES

# Step 1: Team names
async def get_team_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["teams"] = update.message.text
    await update.message.reply_text("What is the league status or importance of the match (e.g., Final, League, Friendly)?")
    return LEAGUE_STATUS

# Step 2: League status
async def get_league_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["league_status"] = update.message.text
    await update.message.reply_text("What are the average goals scored/conceded by each team? (e.g., Arsenal: 1.8/1.1, Chelsea: 1.5/1.3)")
    return AVG_GOALS

# Step 3: Average goals
async def get_avg_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["avg_goals"] = update.message.text
    await update.message.reply_text("What’s their head-to-head record? (e.g., Arsenal won 3, Chelsea won 2, 2 draws)")
    return HEAD_TO_HEAD

# Step 4: Head to Head
async def get_head_to_head(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["head_to_head"] = update.message.text
    await update.message.reply_text("What's the recent form for both teams? (e.g., Arsenal: W-W-L-D-W, Chelsea: L-D-W-W-L)")
    return FORM

# Step 5: Recent Form
async def get_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["form"] = update.message.text

    # Combine and make a dummy prediction
    data = context.user_data
    prediction = f"📊 Prediction Based on Your Input:\n\n" \
                 f"🏟️ Match: {data['teams']}\n" \
                 f"🏆 League Status: {data['league_status']}\n" \
                 f"⚽ Avg Goals: {data['avg_goals']}\n" \
                 f"📈 Head-to-Head: {data['head_to_head']}\n" \
                 f"🔥 Recent Form: {data['form']}\n\n" \
                 f"✅ **Prediction**: The match is likely to be close, but the team with better form and head-to-head advantage has the edge."

    await update.message.reply_text(prediction)
    return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prediction cancelled. Send /start to begin again.")
    return ConversationHandler.END

# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEAM_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_team_names)],
            LEAGUE_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_league_status)],
            AVG_GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_avg_goals)],
            HEAD_TO_HEAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_head_to_head)],
            FORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_form)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
