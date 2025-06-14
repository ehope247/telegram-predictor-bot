import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import re

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(level=logging.INFO)

# --- Prediction logic ---
def analyze_prediction(team_a, team_b, avg_goals_a, avg_goals_b, h2h_a, h2h_b, h2h_d, form_a, form_b):
    result = "\n✅ Prediction Complete:\n"
    result += f"\nTeams: {team_a} vs {team_b}"
    result += f"\nAvg Goals: {team_a}: {avg_goals_a}, {team_b}: {avg_goals_b}"
    result += f"\nHead-to-Head: {team_a} won {h2h_a}, {team_b} won {h2h_b}, Draws: {h2h_d}"
    result += f"\nForm: {team_a}: {form_a}, {team_b}: {form_b}\n"

    # Calculate form points (W=3, D=1, L=0)
    def form_points(form):
        return sum(3 if c == 'W' else 1 if c == 'D' else 0 for c in form)

    points_a = form_points(form_a)
    points_b = form_points(form_b)

    # Winner prediction
    if h2h_b > h2h_a and points_b > points_a:
        likely_winner = team_b
    elif h2h_a > h2h_b and points_a > points_b:
        likely_winner = team_a
    else:
        likely_winner = "Draw or Tight Match"

    result += f"\n🏆 Likely Winner: {likely_winner}"

    # Double Chance
    if likely_winner == team_a:
        double_chance = f"{team_a} or Draw"
    elif likely_winner == team_b:
        double_chance = f"{team_b} or Draw"
    else:
        double_chance = f"Either team or Draw"
    result += f"\n🎯 Double Chance: {double_chance}"

    # Over/Under 2.5 Goals
    avg_total_goals = (avg_goals_a + avg_goals_b) / 2
    if avg_total_goals >= 2.5:
        over_under_tip = "Over 2.5 Goals"
    else:
        over_under_tip = "Under 2.5 Goals"
    result += f"\n⚽ Goal Market: {over_under_tip}"

    return result

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Stats Predictor Bot!\n\nPlease send the following details separated by commas:\n\nTeam A name, Team B name, League status (e.g. 'Yes'), Team A avg goals scored/conceded, Team B avg goals scored/conceded, H2H (A wins,B wins,draws), Team A form (e.g. WWWDL), Team B form (e.g. LLWDD)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    try:
        parts = [p.strip() for p in msg.split(',')]
        if len(parts) != 8:
            raise ValueError("Incorrect number of inputs. Please provide 8 comma-separated values.")

        team_a, team_b = parts[0], parts[1]
        league_status = parts[2]

        avg_goals = parts[3].split('/')
        avg_goals_a = float(avg_goals[0])
        avg_goals_b = float(avg_goals[1])

        h2h = parts[5].split('/')
        h2h_a, h2h_b, h2h_d = int(h2h[0]), int(h2h[1]), int(h2h[2])

        form_a = parts[6].upper()
        form_b = parts[7].upper()

        prediction = analyze_prediction(team_a, team_b, avg_goals_a, avg_goals_b, h2h_a, h2h_b, h2h_d, form_a, form_b)
        await update.message.reply_text(prediction)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}\nPlease follow the format and try again.")

# --- App Setup ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    print("Bot starting...")
    app.run_polling()
    
