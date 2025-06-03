import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from datetime import datetime
from collections import defaultdict

# .env fayldan tokenni yuklaymiz
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logger sozlamasi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Foydalanuvchilar ma'lumotlarini saqlash uchun in-memory dict
users_data = defaultdict(lambda: defaultdict(list))  # user_id -> date -> list of entries

# Conversation states
DAROMAD = 1

def format_date():
    return datetime.now().strftime("%d/%m/%Y")

def format_time():
    return datetime.now().strftime("%H:%M")

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📒 Harajatlaringizni yozing.\n"
        "Daromad qo'shish uchun /daromad buyrug'ini bosing.\n"
        "Bugungi yozuvlarni ko‘rish uchun /today buyrug‘idan foydalaning."
    )

# /daromad komandasi boshlovi
async def daromad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Qancha daromad qo'shmoqchisiz? (faqat raqam)")
    return DAROMAD

# Daromadni qabul qilish
async def daromad_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        summa = float(text)
    except ValueError:
        await update.message.reply_text("Iltimos, faqat raqam kiriting.")
        return DAROMAD

    today = format_date()
    entry = f"[💰 DAROMAD] {summa} so'm - {format_time()}"
    users_data[user_id][today].append(entry)
    await update.message.reply_text("✅ Daromad qo‘shildi.")
    return ConversationHandler.END

# /cancel komandasi — bekor qilish
async def bekor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

# Bugungi kun yozuvlarini ko‘rsatish
async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = format_date()
    entries = users_data[user_id].get(today, [])
    if not entries:
        await update.message.reply_text("📭 Bugun yozuvlar yo'q.")
        return
    text = f"📅 Bugungi yozuvlar ({today}):\n\n" + "\n".join(entries)
    await update.message.reply_text(text)

# Harajatni qabul qilish (to‘g‘ridan-to‘g‘ri matn shaklida)
async def xarajat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not text:
        return
    today = format_date()
    entry = f"[💸 HARJ] {text} - {format_time()}"
    users_data[user_id][today].append(entry)

    # Yangi yozuv bilan birga barcha bugungi yozuvlarni ko‘rsatamiz
    all_entries = "\n".join(users_data[user_id][today])
    await update.message.reply_text(f"📒 Yozildi:\n{all_entries}")

# Botni ishga tushurish qismi
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", show_today))

    daromad_conv = ConversationHandler(
        entry_points=[CommandHandler("daromad", daromad_start)],
        states={
            DAROMAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, daromad_qabul)]
        },
        fallbacks=[CommandHandler("cancel", bekor)],
    )
    app.add_handler(daromad_conv)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, xarajat))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
