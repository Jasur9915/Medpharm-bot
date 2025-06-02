import sqlite3
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from dotenv import load_dotenv

# .env faylidan API_TOKEN ni o‘qish
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    raise ValueError("API_TOKEN .env faylida topilmadi. Iltimos, .env faylida API_TOKEN ni sozlang.")

# Ma'lumotlar bazasini sozlash
def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, amount INTEGER, category TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Xarajat matnini tahlil qilish
def parse_expense(text):
    pattern = r'(\w+)\s+(\d+)'
    matches = re.findall(pattern, text)
    return [(item, int(amount)) for item, amount in matches]

# Xarajatlarni avtomatik saqlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    expenses = parse_expense(text)
    if expenses:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        date = datetime.now().strftime('%Y-%m-%d')
        for item, amount in expenses:
            c.execute("INSERT INTO transactions (user_id, type, amount, category, date) VALUES (?, ?, ?, ?, ?)",
                      (user_id, 'expense', amount, item, date))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Xarajatlar saqlandi: {', '.join([f'{item}: {amount}' for item, amount in expenses])}")
        await show_balance(update, context)

# Daromad qo‘shish
async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        args = context.args
        amount = int(args[0])
        category = ' '.join(args[1:]) or 'Umumiy'
        date = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, category, date) VALUES (?, ?, ?, ?, ?)",
                  (user_id, 'income', amount, category, date))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Daromad saqlandi: {amount} ({category})")
        await show_balance(update, context)
    except (IndexError, ValueError):
        await update.message.reply_text("Iltimos, to‘g‘ri formatda kiriting: /daromad <miqdor> <kategoriya>")

# Balansni ko‘rsatish
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND date = ? GROUP BY type", (user_id, date))
    results = c.fetchall()
    conn.close()

    income = 0
    expense = 0
    for t_type, amount in results:
        if t_type == 'income':
            income = amount or 0
        elif t_type == 'expense':
            expense = amount or 0

    balance = income - expense
    await update.message.reply_text(f"Kunlik hisob:\nJami daromad: {income}\nJami xarajat: {expense}\nBalans: {balance}")

# Xarajatlarni tahrirlash
async def edit_xarajat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        args = context.args
        transaction_id = int(args[0])
        new_amount = int(args[1]) if len(args) > 1 else None
        new_category = ' '.join(args[2:]) if len(args) > 2 else None

        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM transactions WHERE id = ?", (transaction_id,))
        result = c.fetchone()
        
        if not result or result[0] != user_id:
            await update.message.reply_text("Bu tranzaksiya sizga tegishli emas yoki topilmadi!")
            conn.close()
            return

        update_query = "UPDATE transactions SET"
        update_params = []
        if new_amount is not None:
            update_query += " amount = ?,"
            update_params.append(new_amount)
        if new_category is not None:
            update_query += " category = ?,"
            update_params.append(new_category)
        
        update_query = update_query.rstrip(',') + " WHERE id = ? AND user_id = ?"
        update_params.extend([transaction_id, user_id])
        
        c.execute(update_query, update_params)
        conn.commit()
        conn.close()
        await update.message.reply_text("Xarajat muvaffaqiyatli tahrirlandi!")
        await show_balance(update, context)
    except (IndexError, ValueError):
        await update.message.reply_text("Iltimos, to‘g‘ri formatda kiriting: /edit <tranzaksiya_id> <yangi_miqdor> <yangi_kategoriya>")

# Statistika
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("SELECT type, SUM(amount), COUNT(*) FROM transactions WHERE user_id = ? GROUP BY type", (user_id,))
    results = c.fetchall()
    conn.close()

    response = "Umumiy statistika:\n"
    income = expense = 0
    income_count = expense_count = 0
    for t_type, amount, count in results:
        if t_type == 'income':
            income = amount or 0
            income_count = count
        elif t_type == 'expense':
            expense = amount or 0
            expense_count = count

    response += f"Daromadlar: {income} (Jami {income_count} ta)\n"
    response += f"Xarajatlar: {expense} (Jami {expense_count} ta)\n"
    response += f"Balans: {income - expense}"
    await update.message.reply_text(response)

# Hisobot tugmalari
def get_report_buttons():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Kunlik PDF", callback_data='daily_pdf')],
        [InlineKeyboardButton("Haftalik PDF", callback_data='weekly_pdf')],
        [InlineKeyboardButton("Oylik PDF", callback_data='monthly_pdf')],
        [InlineKeyboardButton("Jami hisob", callback_data='total_balance')]
    ])
    return keyboard

async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hisobot turini tanlang:", reply_markup=get_report_buttons())

# PDF hisobot generatsiyasi
def generate_pdf(user_id, period):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    today = datetime.now()
    if period == 'daily':
        date = today.strftime('%Y-%m-%d')
        c.execute("SELECT type, amount, category, date FROM transactions WHERE user_id = ? AND date = ?",
                  (user_id, date))
    elif period == 'weekly':
        start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=6 - today.weekday())).strftime('%Y-%m-%d')
        c.execute("SELECT type, amount, category, date FROM transactions WHERE user_id = ? AND date BETWEEN ? AND ?",
                  (user_id, start_date, end_date))
    elif period == 'monthly':
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.replace(day=28).strftime('%Y-%m-%d')
        c.execute("SELECT type, amount, category, date FROM transactions WHERE user_id = ? AND date BETWEEN ? AND ?",
                  (user_id, start_date, end_date))

    transactions = c.fetchall()
    conn.close()

    filename = f"{period}_report_{user_id}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, f"{period.capitalize()} Hisobot")
    y = 700
    total_income = 0
    total_expense = 0
    for t_type, amount, category, date in transactions:
        c.drawString(100, y, f"{t_type.capitalize()}: {category} - {amount} ({date})")
        if t_type == 'income':
            total_income += amount
        else:
            total_expense += amount
        y -= 20
    c.drawString(100, y - 20, f"Jami daromad: {total_income}")
    c.drawString(100, y - 40, f"Jami xarajat: {total_expense}")
    c.drawString(100, y - 60, f"Balans: {total_income - total_expense}")
    c.save()
    return filename

async def process_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    period = update.callback_query.data.split('_')[0]

    if update.callback_query.data == 'total_balance':
        await show_balance(update.callback_query, context)
    else:
        filename = generate_pdf(user_id, period)
        with open(filename, 'rb') as file:
            await update.callback_query.message.reply_document(file, caption=f"{period.capitalize()} hisobot")
        os.remove(filename)

    await update.callback_query.answer()

# Guruh hisobi
async def group_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute("SELECT user_id, SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income, "
                  "SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense "
                  "FROM transactions WHERE date = ? GROUP BY user_id",
                  (datetime.now().strftime('%Y-%m-%d'),))
        results = c.fetchall()
        conn.close()

        response = "Guruh hisobi (bugun):\n"
        for user_id, income, expense in results:
            response += f"Foydalanuvchi {user_id}: Daromad: {income or 0}, Xarajat: {expense or 0}, Balans: {(income or 0) - (expense or 0)}\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Bu buyruq faqat guruhlarda ishlaydi.")

# Kun yangilanishini tekshirish
async def check_new_day(context: ContextTypes.DEFAULT_TYPE):
    current_date = datetime.now().strftime('%Y-%m-%d')
    # Yangi kun boshlanganda maxsus logika qo‘shish mumkin
    pass

def main():
    app = Application.builder().token(API_TOKEN).build()

    # Buyruqlar va xabarlar ishlovchilari
    app.add_handler(CommandHandler("daromad", add_income))
    app.add_handler(CommandHandler("hisobot", report_menu))
    app.add_handler(CommandHandler("guruh_hisob", group_balance))
    app.add_handler(CommandHandler("edit", edit_xarajat))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.Text() & ~filters.Command(), handle_message))
    app.add_handler(CallbackQueryHandler(process_callback))

    # Kun yangilanishini tekshirish
    app.job_queue.run_repeating(check_new_day, interval=60, first=0)

    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
