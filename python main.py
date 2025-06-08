import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from fpdf import FPDF
from dotenv import load_dotenv

# .env faylidan API_TOKEN ni o'qish
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN", "8116269873:AAEnl9QCBTFxT0xxySuKshd5lHIJ3Ybi1Lg")

# Ma'lumotlar bazasini sozlash
def init_db():
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    category TEXT,
                    description TEXT,
                    date TEXT,
                    time TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS incomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    description TEXT,
                    date TEXT,
                    time TEXT
                 )''')
    conn.commit()
    conn.close()

# Harajat qo'shish
async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Iltimos, harajat miqdorini yozing (masalan: 50000):")
    context.user_data["state"] = "awaiting_expense_amount"

# Daromad qo'shish
async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Iltimos, daromad miqdorini yozing (masalan: 1000000):")
    context.user_data["state"] = "awaiting_income_amount"

# Kategoriyalarni tanlash
def get_category_keyboard():
    categories = ["Oziq-ovqat", "Transport", "Kommunal", "Kiyim", "Sog‘liq", "Boshqa"]
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}") for cat in categories[i:i+2]] for i in range(0, len(categories), 2)]
    return InlineKeyboardMarkup(keyboard)

# Xabarlar bilan ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    state = context.user_data.get("state")

    if state == "awaiting_expense_amount":
        try:
            amount = float(text)
            context.user_data["expense_amount"] = amount
            context.user_data["state"] = "awaiting_category"
            await update.message.reply_text("Kategoriyani tanlang:", reply_markup=get_category_keyboard())
        except ValueError:
            await update.message.reply_text("Iltimos, to‘g‘ri miqdor kiriting (masalan: 50000).")
    
    elif state == "awaiting_income_amount":
        try:
            amount = float(text)
            context.user_data["income_amount"] = amount
            context.user_data["state"] = "awaiting_income_description"
            await update.message.reply_text("Daromad haqida qisqacha ma'lumot yozing (masalan: Ish haqi):")
        except ValueError:
            await update.message.reply_text("Iltimos, to‘g‘ri miqdor kiriting (masalan: 1000000).")
    
    elif state == "awaiting_income_description":
        description = text
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M")
        conn = sqlite3.connect("expenses.db")
        c = conn.cursor()
        c.execute("INSERT INTO incomes (user_id, amount, description, date, time) VALUES (?, ?, ?, ?, ?)",
                  (user_id, context.user_data["income_amount"], description, date, time))
        conn.commit()
        conn.close()
        await update.message.reply_text("Daromad muvaffaqiyatli qo‘shildi!")
        context.user_data.clear()

# Kategoriya tanlash
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    context.user_data["category"] = category
    context.user_data["state"] = "awaiting_description"
    await query.message.reply_text("Harajat haqida qisqacha ma'lumot yozing (masalan: Non sotib oldim):")

# Tavsifni saqlash
async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    description = update.message.text
    amount = context.user_data["expense_amount"]
    category = context.user_data["category"]
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M")
    
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("INSERT INTO expenses (user_id, amount, category, description, date, time) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, amount, category, description, date, time))
    conn.commit()
    conn.close()
    
    await update.message.reply_text("Harajat muvaffaqiyatli qo‘shildi!")
    context.user_data.clear()

# Hisobot yaratish (PDF)
async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    period = context.args[0] if context.args else "kunlik"
    
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    
    if period == "kunlik":
        start_date = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT * FROM expenses WHERE user_id = ? AND date = ?", (user_id, start_date))
        expenses = c.fetchall()
        c.execute("SELECT * FROM incomes WHERE user_id = ? AND date = ?", (user_id, start_date))
        incomes = c.fetchall()
    elif period == "haftalik":
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        c.execute("SELECT * FROM expenses WHERE user_id = ? AND date >= ?", (user_id, start_date))
        expenses = c.fetchall()
        c.execute("SELECT * FROM incomes WHERE user_id = ? AND date >= ?", (user_id, start_date))
        incomes = c.fetchall()
    elif period == "oylik":
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        c.execute("SELECT * FROM expenses WHERE user_id = ? AND date >= ?", (user_id, start_date))
        expenses = c.fetchall()
        c.execute("SELECT * FROM incomes WHERE user_id = ? AND date >= ?", (user_id, start_date))
        incomes = c.fetchall()
    
    conn.close()
    
    # PDF yaratish
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{period.capitalize()} Hisobot", ln=True, align="C")
    
    pdf.cell(200, 10, txt="Harajatlar:", ln=True)
    total_expense = 0
    for i, expense in enumerate(expenses, 1):
        amount, category, desc, date, time = expense[2], expense[3], expense[4], expense[5], expense[6]
        total_expense += amount
        pdf.cell(200, 10, txt=f"{i}. {date} {time} - {category}: {desc} - {amount} UZS", ln=True)
    
    pdf.cell(200, 10, txt=f"Umumiy harajat: {total_expense} UZS", ln=True)
    
    pdf.cell(200, 10, txt="Daromadlar:", ln=True)
    total_income = 0
    for i, income in enumerate(incomes, 1):
        amount, desc, date, time = income[2], income[3], income[4], income[5]
        total_income += amount
        pdf.cell(200, 10, txt=f"{i}. {date} {time} - {desc}: {amount} UZS", ln=True)
    
    pdf.cell(200, 10, txt=f"Umumiy daromad: {total_income} UZS", ln=True)
    pdf.cell(200, 10, txt=f"Balans: {total_income - total_expense} UZS", ln=True)
    
    pdf_file = f"{period}_hisobot.pdf"
    pdf.output(pdf_file)
    await update.message.reply_document(document=open(pdf_file, "rb"))
    os.remove(pdf_file)

# Statistika
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category", (user_id,))
    stats = c.fetchall()
    conn.close()
    
    response = "Statistika (kategoriyalar bo‘yicha):\n"
    for category, total in stats:
        response += f"{category}: {total} UZS\n"
    await update.message.reply_text(response or "Hozircha statistika yo‘q.")

# Bosh menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Harajat qo‘shish", callback_data="add_expense")],
        [InlineKeyboardButton("Daromad qo‘shish", callback_data="add_income")],
        [InlineKeyboardButton("Kunlik hisobot", callback_data="report_kunlik")],
        [InlineKeyboardButton("Haftalik hisobot", callback_data="report_haftalik")],
        [InlineKeyboardButton("Oylik hisobot", callback_data="report_oylik")],
        [InlineKeyboardButton("Statistika", callback_data="stats")]
    ]
    await update.message.reply_text("Xush kelibsiz! Quyidagi amallarni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

# Tugma bosilishlarini boshqarish
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "add_expense":
        await add_expense(query, context)
    elif query.data == "add_income":
        await add_income(query, context)
    elif query.data.startswith("report_"):
        period = query.data.replace("report_", "")
        await generate_report(query, context)
    elif query.data == "stats":
        await stats(query, context)
    elif query.data.startswith("cat_"):
        await handle_category(update, context)

def main():
    init_db()
    app = Application.builder().token(API_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
