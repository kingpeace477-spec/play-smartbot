import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
# Try multiple ways to get the token
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# If token is not found, exit with error
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable is not set!")
    print("Please set BOT_TOKEN in Railway Variables")
    print(f"Available environment variables: {list(os.environ.keys())}")
    exit(1)

print(f"✅ Bot token found: {BOT_TOKEN[:10]}... (length: {len(BOT_TOKEN)})")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Quiz Data ---
QUIZ = [
    {
        "question": "What is the capital of France?",
        "options": ["London", "Paris", "Berlin", "Madrid"],
        "answer": 1  # Index of correct answer (0-based)
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
    },
    {
        "question": "Who painted the Mona Lisa?",
        "options": ["Michelangelo", "Leonardo da Vinci", "Raphael", "Donatello"],
        "answer": 1
    },
    {
        "question": "What is the chemical symbol for gold?",
        "options": ["Au", "Ag", "Fe", "Cu"],
        "answer": 0
    }
]

# --- Bot Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with the bot's purpose."""
    user = update.effective_user
    
    welcome_message = (
        f"🧠 Welcome to Play Smrt, {user.first_name}!\n\n"
        "🎯 This bot tests your knowledge with fun quizzes.\n"
        "📚 Learn new facts while having fun!\n\n"
        "Click the button below to start your first quiz:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Start Quiz", callback_data='start_quiz')]
    ])
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=keyboard
    )

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the quiz by initializing user data and asking first question."""
    query = update.callback_query
    await query.answer()
    
    # Reset user's quiz progress
    context.user_data['quiz_step'] = 0
    context.user_data['score'] = 0
    context.user_data['quiz_active'] = True
    
    # Ask the first question
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and sends the current question to the user."""
    step = context.user_data.get('quiz_step', 0)
    
    # Check if quiz is complete
    if step >= len(QUIZ):
        score = context.user_data.get('score', 0)
        total = len(QUIZ)
        
        # Calculate percentage
        percentage = (score / total) * 100
        
        # Personalized message based on score
        if percentage == 100:
            result_message = "🏆 PERFECT SCORE! You're a genius!"
        elif percentage >= 80:
            result_message = "🌟 Excellent work! You really know your stuff!"
        elif percentage >= 60:
            result_message = "👍 Good job! Keep learning!"
        else:
            result_message = "📖 Keep studying! Try again to improve your score!"
        
        final_message = (
            f"🎉 Quiz Complete!\n\n"
            f"📊 Your score: {score} out of {total}\n"
            f"📈 Percentage: {percentage:.0f}%\n\n"
            f"{result_message}\n\n"
            "💡 Use /start to play again"
        )
        
        # Check if we're editing an existing message or sending a new one
        if update.callback_query:
            await update.callback_query.edit_message_text(final_message)
        else:
            await update.message.reply_text(final_message)
        
        context.user_data['quiz_active'] = False
        return
    
    # Get the current question
    q_data = QUIZ[step]
    question_text = f"**Question {step+1}/{len(QUIZ)}**\n\n{q_data['question']}"
    
    # Create inline keyboard with options
    keyboard = []
    option_labels = ["A", "B", "C", "D"]
    for i, option in enumerate(q_data['options']):
        keyboard.append([
            InlineKeyboardButton(
                f"{option_labels[i]}. {option}", 
                callback_data=f'answer_{i}'
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit the question message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            question_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            question_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the user's answer and provides feedback."""
    query = update.callback_query
    await query.answer()
    
    # Check if quiz is still active
    if not context.user_data.get('quiz_active', False):
        await query.edit_message_text(
            "⏰ Your quiz session has ended. Use /start to begin a new quiz!"
        )
        return
    
    # Parse the user's answer
    selected_index = int(query.data.split('_')[1])
    step = context.user_data.get('quiz_step', 0)
    correct_index = QUIZ[step]['answer']
    q_data = QUIZ[step]
    
    # Check answer
    if selected_index == correct_index:
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        feedback = f"✅ Correct! The answer is {q_data['options'][correct_index]}."
    else:
        feedback = f"❌ Incorrect. The correct answer is {q_data['options'][correct_index]}."
    
    # Show feedback
    await query.edit_message_text(
        f"{feedback}\n\n📝 Moving to next question..."
    )
    
    # Move to next question
    context.user_data['quiz_step'] = step + 1
    
    # Wait a moment then show next question
    # We'll use a simple approach by sending the next question immediately
    # But we need to simulate a callback context for ask_question
    await ask_question(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows help information about the bot."""
    help_text = (
        "🤖 **Play Smrt Bot Help**\n\n"
        "📋 **Commands:**\n"
        "/start - Start the bot and see welcome message\n"
        "/help - Show this help message\n"
        "/quiz - Start a new quiz\n\n"
        "🎮 **How to Play:**\n"
        "1. Click 'Start Quiz' or use /quiz\n"
        "2. Answer each question by clicking on an option\n"
        "3. Get immediate feedback on your answers\n"
        "4. See your final score at the end!\n\n"
        "💡 **Tips:**\n"
        "• Take your time - there's no time limit\n"
        "• Try to get all questions right for a perfect score\n"
        "• Use /start anytime to play again"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct command to start a quiz."""
    # Reset user data
    context.user_data['quiz_step'] = 0
    context.user_data['score'] = 0
    context.user_data['quiz_active'] = True
    await ask_question(update, context)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows information about the bot."""
    about_text = (
        "🧠 **About Play Smrt**\n\n"
        "Play Smrt is an interactive quiz bot designed to test your knowledge\n"
        "and help you learn new facts in a fun way.\n\n"
        "📚 **Categories Covered:**\n"
        "• Geography\n"
        "• Science\n"
        "• Art & History\n"
        "• General Knowledge\n\n"
        "🎯 **Mission:**\n"
        "Making learning fun and accessible for everyone!\n\n"
        "🌟 **Version:** 1.0.0"
    )
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def handle_callback_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any errors from callbacks."""
    await update.callback_query.answer(
        "⚠️ Something went wrong. Please try again with /start",
        show_alert=True
    )

# --- Main Application ---

def main():
    """Starts the bot."""
    print("🚀 Starting Play Smrt Bot...")
    print(f"🔑 Using token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("about", about_command))
    
    # Add callback query handler for quiz buttons
    application.add_handler(
        CallbackQueryHandler(start_quiz, pattern='start_quiz')
    )
    application.add_handler(
        CallbackQueryHandler(handle_answer, pattern='answer_')
    )
    
    # Error handler
    application.add_error_handler(handle_callback_error)
    
    print("✅ Bot is ready and listening for messages!")
    print("📱 Find your bot on Telegram and send /start")
    
    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()
