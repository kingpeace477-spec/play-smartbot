import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
# 1. Replace 'YOUR_BOT_TOKEN' with the token from @BotFather.
# 2. It's best practice to use environment variables. We'll set this up on Railway later.
BOT_TOKEN = 'YOUR_BOT_TOKEN' 

# Enable logging to help you debug
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# A simple quiz data structure: question, options, and the correct answer index
QUIZ = [
    {
        "question": "What is the capital of France?",
        "options": ["London", "Paris", "Berlin", "Madrid"],
        "answer": 1
    },
    {
        "question": "Which planet is known as the 'Red Planet'?",
        "options": ["Venus", "Jupiter", "Mars", "Saturn"],
        "answer": 2
    },
    {
        "question": "What is the name of the largest ocean on Earth?",
        "options": ["Atlantic", "Indian", "Arctic", "Pacific"],
        "answer": 3
    }
]

# --- Bot Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and explains the bot's purpose."""
    user = update.effective_user
    await update.message.reply_text(
        f"🧠 Welcome to Play Smrt, {user.first_name}!\n\n"
        "This bot will test your knowledge with a fun, short quiz.\n"
        "To begin, simply click the button below.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Start Quiz", callback_data='start_quiz')]
        ])
    )

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the quiz by asking the first question."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    # Reset the quiz progress for this user
    context.user_data['quiz_step'] = 0
    context.user_data['score'] = 0

    # Ask the first question
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches the current question and sends it."""
    step = context.user_data.get('quiz_step', 0)
    if step >= len(QUIZ):
        # Quiz is finished, show results
        score = context.user_data.get('score', 0)
        await update.callback_query.edit_message_text(
            f"🎉 Quiz Complete!\n\n"
            f"Your score: {score} out of {len(QUIZ)}\n"
            "Thanks for playing! Use /start to play again."
        )
        return

    # Get the current question data
    q_data = QUIZ[step]
    question_text = f"**Question {step+1}/{len(QUIZ)}**\n{q_data['question']}"

    # Create an inline keyboard with the options
    keyboard = []
    for i, option in enumerate(q_data['options']):
        keyboard.append([InlineKeyboardButton(option, callback_data=f'answer_{i}')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Edit the previous message (or send a new one)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            question_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(question_text, reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the user's answer, updates score, and moves to the next question."""
    query = update.callback_query
    await query.answer()

    # Determine which answer the user selected
    selected_index = int(query.data.split('_')[1])
    step = context.user_data.get('quiz_step', 0)
    correct_index = QUIZ[step]['answer']

    # Check if the answer is correct
    if selected_index == correct_index:
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        await query.edit_message_text("✅ Correct! Well done.")
    else:
        await query.edit_message_text(f"❌ That's incorrect. The answer was {QUIZ[step]['options'][correct_index]}.")

    # Prepare the next step
    context.user_data['quiz_step'] = step + 1
    
    # Ask the next question (or show final score)
    # We re-use the ask_question function but we need to simulate a callback_query
    # by storing the query in the context, then calling the function.
    await ask_question(update, context)

# --- Main Execution ---

def main():
    """Starts the bot."""
    # 1. Create the Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # 2. Register command and callback handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start_quiz, pattern='start_quiz'))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern='answer_'))

    # 3. Start the bot (using Polling for simplicity)
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
