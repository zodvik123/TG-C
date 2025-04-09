import telebot
import os
import subprocess

# ==== CONFIG ====
BOT_TOKEN = '7625188166:AAE7oSjBhqN5nU_mi1oF5O9LxzsLd2ASItw'
ADMIN_ID = 7929154249  # replace with your Telegram ID
UPLOAD_DIR = 'uploads'

bot = telebot.TeleBot(BOT_TOKEN)

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

authorized_users = set()
user_gcc_cmds = {}

# ==== /start ====
@bot.message_handler(commands=['start'])
def start(message):
    start_text = (
        "👨‍💻 *Welcome to C Compiler Bot!*\n\n"
        "🚀 *How it works:*\n"
        "1️⃣ Send me a GCC command like:\n`gcc -Wall -O2`\n"
        "2️⃣ Then send your `.c` file\n"
        "💡 I'll compile it and give you the binary or error log.\n\n"
        "🔒 Access is restricted. Contact admin if needed."
    )
    bot.send_message(message.chat.id, start_text, parse_mode='Markdown')

# ==== /add ====
@bot.message_handler(commands=['add'])
def add_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        authorized_users.add(user_id)
        bot.reply_to(message, f"✅ User `{user_id}` added.", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Usage: /add <user_id>")

# ==== /remove ====
@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        authorized_users.discard(user_id)
        bot.reply_to(message, f"❎ User `{user_id}` removed.", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Usage: /remove <user_id>")

# ==== /log ====
@bot.message_handler(commands=['log'])
def send_logs(message):
    if message.from_user.id != ADMIN_ID:
        return
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.c')]
    if not files:
        bot.reply_to(message, "📭 No .c files found.")
    else:
        for f in files:
            with open(os.path.join(UPLOAD_DIR, f), 'rb') as file:
                bot.send_document(ADMIN_ID, file)

# ==== GCC command handler ====
@bot.message_handler(func=lambda m: m.text and m.text.startswith("gcc"))
def handle_gcc(message):
    if message.from_user.id not in authorized_users and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🔒 You are not authorized. Contact admin.")
        return

    user_gcc_cmds[message.from_user.id] = message.text
    bot.reply_to(message, "✅ GCC command saved. Now send me your `.c` file.")

# ==== C file upload handler ====
@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id

    if user_id not in authorized_users and user_id != ADMIN_ID:
        bot.reply_to(message, "🔒 You are not authorized. Contact admin.")
        return

    if user_id not in user_gcc_cmds:
        bot.reply_to(message, "❗ Please send a GCC command first (e.g., `gcc -Wall`).")
        return

    file_info = bot.get_file(message.document.file_id)
    filename = message.document.file_name

    if not filename.endswith(".c"):
        bot.reply_to(message, "❌ Only `.c` files are supported.")
        return

    c_file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{filename}")
    with open(c_file_path, 'wb') as f:
        f.write(bot.download_file(file_info.file_path))

    # Forward to admin
    with open(c_file_path, 'rb') as fwd:
        bot.send_document(ADMIN_ID, fwd, caption=f"📥 File from `{user_id}`", parse_mode='Markdown')

    # Compile
    output_path = c_file_path.replace(".c", "")
    gcc_cmd = user_gcc_cmds[user_id].split() + [c_file_path, "-o", output_path]

    try:
        result = subprocess.run(gcc_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            bot.reply_to(message, "✅ Compiled successfully. Sending binary...")
            with open(output_path, 'rb') as bin_file:
                bot.send_document(message.chat.id, bin_file)
        else:
            bot.reply_to(message, "❌ Compilation failed:\n```\n" + result.stderr + "\n```", parse_mode='Markdown')

    except subprocess.TimeoutExpired:
        bot.reply_to(message, "⏱️ Compilation timed out.")

    # Cleanup
    try:
        os.remove(c_file_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        del user_gcc_cmds[user_id]
    except:
        pass

# ==== Start polling ====
print("🤖 Bot is running...")
bot.polling()
