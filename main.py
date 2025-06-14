import logging
import re
import os
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is live!"

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    instructions = (
        "Please enter the match data in the following format:\n"
        "*Team A* vs *Team B*\n"
        "Avg goals scored A, Avg goals conceded A, Avg goals scored B, Avg goals conceded B\n"
        "Form A (last 5) vs Form B (last 5) (e.g., WWDWL vs LWDWL)\n"
        "Head-to-head results (e.g., WWLDW)\n\n"
        "*Example:* \n"
        "Aston Villa vs Liverpool\n"
        "1.2, 1.3, 1.5, 1.1\n"
        "WWDWL vs LWDWL\n"
        "WWLDW"
    )
    await update.message.reply_text(instructions, parse_mode=ParseMode.MARKDOWN)

# Prediction message handler
async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    try:
        # Find first numeric value to separate team names from stats
        match = re.search(r"[0-9]+(?:\.[0-9]+)?", text)
        if not match:
            raise ValueError("No numeric stats found in the message.")
        team_section = text[: match.start()]
        # Parse team names around " vs "
        team_split = re.split(r"\s+vs\s+", team_section, flags=re.IGNORECASE)
        if len(team_split) < 2:
            raise ValueError("Format error: could not split team names.")
        teamA = team_split[0].strip()
        teamB = team_split[1].strip()

        # Parse numeric values (avg goals scored/conceded)
        nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", text)
        if len(nums) < 4:
            raise ValueError("Not enough numeric values provided for goals.")
        gsa, gca, gsb, gcb = map(float, nums[:4])

        # Parse form sequences (last 5 games, e.g., "WWDWL vs LWDWL")
        forms = re.findall(r"\b[WDL]{5}\b", text.upper())
        if len(forms) < 3:
            raise ValueError("Could not find valid form or head-to-head data.")
        formA, formB, h2h = forms[0], forms[1], forms[2]

        # Compute expected goals (simple model: average of attack and defense strengths)
        expA = (gsa + gcb) / 2.0
        expB = (gsb + gca) / 2.0

        # Adjust for recent form (difference in number of wins)
        diff_form = formA.count('W') - formB.count('W')

        # Adjust for head-to-head (Team A perspective: W vs L)
        diff_h2h = h2h.count('W') - h2h.count('L')

        # Final estimated scores with small adjustments
        finalA = expA + 0.1 * diff_form + 0.1 * diff_h2h
        finalB = expB - 0.1 * diff_form - 0.1 * diff_h2h

        # Predict match result
        if finalA > finalB + 0.25:
            result = "Home Win"
        elif finalB > finalA + 0.25:
            result = "Away Win"
        else:
            result = "Draw"

        # Predict Over/Under 2.5 goals
        total_exp = finalA + finalB
        ou = "Over 2.5" if total_exp >= 2.5 else "Under 2.5"

        # Predict Both Teams to Score (BTTS)
        btts = "Yes" if finalA > 0.5 and finalB > 0.5 else "No"

        # Format Markdown response
        response = (
            f"*Match:* {teamA} vs {teamB}\n"
            f"*Result:* {result}\n"
            f"*Over/Under 2.5 Goals:* {ou}\n"
            f"*Both Teams to Score:* {btts}"
        )
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error("Error parsing or predicting: %s", e)
        error_msg = (
            "⚠️ *Invalid input format.*\n\n"
            "Please ensure you provide match data in the specified format. Use /start for help."
        )
        await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not set.")
        return

    # Build the Telegram application
    application = ApplicationBuilder().token(token).build()
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, predict))

    # Start bot polling in a separate thread
    import threading
    bot_thread = threading.Thread(target=lambda: application.run_polling(bootstrap_retries=0))
    bot_thread.start()

    # Start Flask app (health check)
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
