import os
import logging
import json
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

# --- Ma'lumotlarni saqlash uchun fayl ---
DATA_FILE = "userdata.json"

# --- Holatlar ---
HARAJAT, DAROMAD, EDIT_SELECT, EDIT_TEXT = range(4)

# --- Kategoriyalar ro'yxati ---
CATEGORIES = ["Oziq-ovqat", "Transport", "Uy-joy", "Sog'liq", "Boshqa"]

# --- Yordamchi funksiyalar ---

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_data(user_id):
    data = load_data()
    user_str = str(user_id)
    if user_str not in data:
        data[user_str] = {"expenses": [], "incomes": []}
    return data

def update_user_data(user_id, key, entry):
    data = load_data()
    user_str = str(user_id)
    if user_str not in data:
        data[user_str] = {"expenses": [], "incomes": []}
    data[user_str][key].append(entry)
    save_data(data)

def parse_amount_category(text):
    parts = text.strip().split()
    amount = None
    category = "Boshqa"
    for part in parts:
        try:
            amount = float(part.replace(",", "."))
            idx = parts.index(part)
            if idx + 1 < len(parts) and parts[idx+1].capitalize() in CATEGORIES:
                category = parts[idx+1].capitalize()
            elif idx - 1 >= 0 and parts[idx-1].capitalize() in CATEGORIES:
                category = parts[idx-1].capitalize()
            break
        except:
            continue
    if amount is None:
        amount = 0
    return amount, category

def create_pdf_report(entries, title="Hisobot"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 40, title)

    c.setFont("Helvetica", 12)
    y = height - 80
    total = 0

    for e in entries:
        date_str = e["date"]
        line = f"{date_str} | {e['category']} | {e['text']} | {e['amount']:.2f} UZS"
        c.drawString(30, y, line)
        y -= 20
        total += e["amount"]
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y - 10, f"Jami: {total:.2f} UZS")
    c.save()
    buffer.seek(0)
    return buffer

# --- Bot handlerlari ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([
        [KeyboardButton("/harajat"), KeyboardButton("/daromad")],
        [KeyboardButton("/hisobot")]
    ], resize_keyboard=True)
    await update.message.reply_text(
        "Salom! Men sizning harajat va daromadlaringizni boshqaraman.\n\n"
        "/harajat - harajat qo'shish\n"
        "/daromad - daromad qo'shish\n"
        "/hisobot - hisobot olish\n"
        "/help - yordam\n",
        reply_markup=kb
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/harajat - Harajat qo'shish\n"
        "/daromad - Daromad qo'shish\n"
        "/hisobot - Kunlik yoki oylik hisobot\n"
        "Harajat va daromadni shu formatda kiriting:\n"
        "12000 oziq-ovqat\n"
        "Summa va kategoriya yozish mumkin"
    )

# --- Harajat qo'shish ---

async def harajat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Harajatni shunday yozing: 12000 oziq-ovqat")
    return HARAJAT

async def harajat_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    amount, category = parse_amount_category(text)
    entry = {
        "text": text,
        "amount": amount,
        "category": category,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    update_user_data(user_id, "expenses", entry)

    # Ko'rsatish
    data = load_data()
    expenses = data[str(user_id)]["expenses"]
    msg = "\n".join([f"{e['date']} | {e['category']} | {e['text']} | {e['amount']}" for e in expenses])
    await update.message.reply_text(f"Harajatlaringiz:\n{msg}")
    return ConversationHandler.END

# --- Daromad qo'shish ---

async def daromad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Daromadni shunday yozing: 50000 maosh")
    return DAROMAD

async def daromad_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    amount, category = parse_amount_category(text)
    entry = {
        "text": text,
        "amount": amount,
        "category": category,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    update_user_data(user_id, "incomes", entry)

    data = load_data()
    incomes = data[str(user_id)]["incomes"]
    msg = "\n".join([f"{e['date']} | {e['category']} | {e['text']} | {e['amount']}" for e in incomes])
    await update.message.reply_text(f"Daromadlaringiz:\n{msg}")
    return ConversationHandler.END

# --- Hisobot tanlash ---

async def hisobot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Kunlik", callback_data="daily")],
        [Inline
