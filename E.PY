import os
import subprocess
from uuid import uuid4
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = "7647291159:AAFH9k3xISuwKR7nP4D0dzOqJfcgPKSXGpU"
C_DIR = "c_uploads"
BIN_DIR = "compiled_bins"
user_files = {}

os.makedirs(C_DIR, exist_ok=True)
os.makedirs(BIN_DIR, exist_ok=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("📥 Send a `.c` file and then use /gcc or `gcc filename.c` to compile.")

def handle_c_file(update: Update, context: CallbackContext):
    doc = update.message.document
    if not doc.file_name.endswith('.c'):
        update.message.reply_text("❌ Only `.c` files are allowed.")
        return

    user_id = update.effective_user.id
    safe_filename = f"{uuid4()}_{doc.file_name}"
    file_path = os.path.join(C_DIR, safe_filename)
    doc.get_file().download(file_path)

    user_files[user_id] = {
        "original_name": doc.file_name,
        "path": file_path
    }

    update.message.reply_text(f"✅ File `{doc.file_name}` received. Now send:\n`/gcc` or `gcc {doc.file_name}`", parse_mode="Markdown")

def handle_gcc(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    args = context.args

    if user_id not in user_files:
        update.message.reply_text("⚠️ Please upload a `.c` file first.")
        return

    file_info = user_files[user_id]
    original_name = file_info["original_name"]
    full_path = file_info["path"]

    if args and args[0] != original_name:
        update.message.reply_text(f"❌ Please use the correct filename: `gcc {original_name}`", parse_mode="Markdown")
        return

    output_path = os.path.join(BIN_DIR, os.path.splitext(os.path.basename(full_path))[0])
    
    try:
        result = subprocess.run(["gcc", full_path, "-o", output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)

        if result.returncode == 0:
            with open(output_path, "rb") as bin_file:
                update.message.reply_document(InputFile(bin_file, filename=os.path.basename(output_path)))
        else:
            update.message.reply_text(f"❌ Compilation error:\n```\n{result.stderr.decode()}\n```", parse_mode="Markdown")

    except subprocess.TimeoutExpired:
        update.message.reply_text("⏱️ Compilation timed out.")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document & Filters.document.file_name.regex(r'\.c$'), handle_c_file))
    dp.add_handler(CommandHandler("gcc", handle_gcc))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^gcc\s+.+\.c$'), lambda update, ctx: handle_gcc(update, ctx)))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
