import os import logging from dotenv import load_dotenv from telegram import Update, ReplyKeyboardMarkup, KeyboardButton from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler from datetime import datetime from collections import defaultdict

load_dotenv() BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

In-memory storage

users_data = defaultdict(lambda: defaultdict(list))  # user_id: {date: [expenses]}

DAROMAD, = range(1)

def format_date(): return datetime.now().strftime("%d/%m/%Y")

def format_time(): return datetime.now().strftime("%H:%M")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📒 Harajatlarni yozing. Daromad uchun /daromad buyrug'ini bosing.")

async def daromad_start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("💰 Qancha daromad kiritmoqchisiz?") return DAROMAD

async def daromad_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id amount = update.message.text try: summa = float(amount) except ValueError: await update.message.reply_text("Iltimos, raqam yuboring.") return DAROMAD

today = format_date()
entry = f"[💰 DAROMAD] {summa} so'm - {format_time()}"
users_data[user_id][today].append(entry)
await update.message.reply_text("✅ Daromad saqlandi.")
return ConversationHandler.END

async def bekor(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("❌ Bekor qilindi.") return ConversationHandler.END

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id today = format_date() data = users_data[user_id].get(today, []) if not data: await update.message.reply_text("📭 Bugun yozuv yo‘q.") else: text = f"📅 Bugungi yozuvlar ({today}):\n\n" + "\n".join(data) await update.message.reply_text(text)

async def xarajat(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id text = update.message.text.strip() if not text: return today = format_date() entry = f"[💸 HARJ] {text} - {format_time()}" users_data[user_id][today].append(entry)

all_entries = "\n".join(users_data[user_id][today])
await update.message.reply_text(f"📒 Yozildi:\n{all_entries}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("today", show_today))

daromad_conv = ConversationHandler( entry_points=[CommandHandler("daromad", daromad_start)], states={ DAROMAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, daromad_qabul)] }, fallbacks=[CommandHandler("cancel", bekor)] )

app.add_handler(daromad_conv) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, xarajat))

if name == 'main': print("Bot ishga tushdi...") app.run_polling()

