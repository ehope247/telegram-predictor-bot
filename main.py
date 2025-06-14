import logging
import re
import os
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask for health check
app = Flask(__name__)
@app.route('/')
def index():
    return "Bot is alive!"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Send match data like this:\n\n"
        "*Team A* vs *Team B*\n"
        "1.2, 1.3, 1.5, 1.1\n"
        "WWDWL vs LWDWL\n"
        "WWLDW\n\n"
        "Use /start to see format again."
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# Prediction handler
async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        match = re.search(r"[0-9]+(?:\.[0-9]+)?", text)
        if not match:
            raise ValueError("Missing stats.")
        
        team_part = text[:match.start()]
        teams = re.split(r"\s+vs\s+", team_part, flags=re.IGNORECASE)
        if len(teams) != 2:
            raise ValueError("Invalid team names.")
        teamA, teamB = teams[0].strip(), teams[1].strip()

        nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", text)
        if len(nums) < 4:
            raise ValueError("Not enough goal stats.")
        gsa, gca, gsb, gcb = map(float, nums[:4])

        forms = re.findall(r"\b[WDL]{5}\b", text.upper())
        if len(forms) < 3:
            raise ValueError("Missing form or H2H data.")
        formA, formB, h2h = forms[:3]

        # Predictions
        expA = (gsa + gcb) / 2
        expB = (gsb + gca) / 2
        form_diff = formA.count("W") - formB.count("W")
        h2h_diff = h2h.count("W") - h2h.count("L")

        finalA = expA + 0.1 * form_diff + 0.1 * h2h_diff
        finalB = expB - 0.1 * form_diff - 0.1 * h2h_diff

        if finalA > finalB + 0.25:
            result = "Home Win"
        elif finalB > finalA + 0.25:
            result = "Away Win"
        else:
            result = "Draw"

        ou = "Over 2.5" if finalA + finalB >= 2.5 else "Under 2.5"
        btts = "Yes" if finalA > 0.5 and finalB > 0.5 else "No"

        prediction = (
            f"*Match:* {teamA} vs {teamB}\n"
            f"*Prediction:* {result}\n"
            f"*Over/Under 2.5:* {ou}\n"
            f"*BTTS:* {btts}"
        )
        await update.message.reply_text(prediction, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Please use the correct format. Use /start for help.")

# Run bot
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not set")
        return

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, predict))

    import threading
    threading.Thread(target=lambda: application.run_polling()).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
