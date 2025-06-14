from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Football Predictor Bot!\n\n"
        "Please enter match details in this format:\n\n"
        "Team 1: Chelsea\n"
        "Team 2: Arsenal\n"
        "League Importance: High\n"
        "Avg Goals Scored: 1.8, 2.0\n"
        "Avg Goals Conceded: 1.2, 1.4\n"
        "Head to Head: Chelsea 2-1 Arsenal\n"
        "Home Form: W W D L W\n"
        "Away Form: L D W W L"
    )

# Function to score form string
def score_form(form_str):
    score_map = {'W': 3, 'D': 1, 'L': 0}
    results = form_str.strip().upper().split()
    return sum(score_map.get(r, 0) for r in results)

# Predict command (when user sends data)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lines = text.strip().split('\n')
    data = {}

    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip().lower()] = value.strip()

    try:
        team1 = data['team 1']
        team2 = data['team 2']
        league = data.get('league importance', 'Unknown')
        goals_scored = [float(x.strip()) for x in data.get('avg goals scored', '0, 0').split(',')]
        goals_conceded = [float(x.strip()) for x in data.get('avg goals conceded', '0, 0').split(',')]
        head_to_head = data.get('head to head', 'N/A')
        home_form = data.get('home form', '')
        away_form = data.get('away form', '')

        home_score = score_form(home_form)
        away_score = score_form(away_form)

        # Simple prediction logic
        t1_strength = goals_scored[0] - goals_conceded[0] + home_score
        t2_strength = goals_scored[1] - goals_conceded[1] + away_score

        if t1_strength > t2_strength:
            prediction = f"{team1} is more likely to win."
        elif t2_strength > t1_strength:
            prediction = f"{team2} is more likely to win."
        else:
            prediction = "It could be a draw."

        reply = (
            f"📊 *Match Preview:*\n"
            f"{team1} vs {team2}\n"
            f"🏆 League: {league}\n\n"
            f"🔢 Avg Goals Scored: {team1}: {goals_scored[0]}, {team2}: {goals_scored[1]}\n"
            f"🛡 Avg Goals Conceded: {team1}: {goals_conceded[0]}, {team2}: {goals_conceded[1]}\n"
            f"🔙 Head to Head: {head_to_head}\n"
            f"🏠 Home Form ({team1}): {home_form} → Score: {home_score}\n"
            f"🚗 Away Form ({team2}): {away_form} → Score: {away_score}\n\n"
            f"💡 *Prediction:* {prediction}"
        )

        await update.message.reply_text(reply, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error parsing input. Make sure you follow the format.\n\nError: {str(e)}")

# Main entry point
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
