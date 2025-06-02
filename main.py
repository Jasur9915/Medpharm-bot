import sqlite3
import re
from datetime import datetime, timedelta
from calendar import monthrange
from contextlib import contextmanager
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

# Ma'lumotlar bazasi ulanishini boshqarish uchun kontekst menejeri
@contextmanager
def get_db_connection():
    conn = sqlite3.connect('finance.db')
    try:
        yield conn
    finally:
        conn.close()

# Ma'lumotlar bazasini sozlash
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, amount INTEGER, category TEXT, date TEXT)''')
        conn.commit()

init_db()

# Xarajat matnini tahlil qilish (bir nechta so‘zli kategoriyalarni qo‘llab-quvvatlash)
def parse_expense(text):
    pattern = r'(.+?)\s+(\d+)$'
    matches = re.findall(pattern, text)
    return [(item.strip(), int(amount)) for item, amount in matches]

# Xarajatlarni avtomatik saqlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    expenses = parse_expense(text)
    if expenses:
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                date = datetime.now().strftime('%Y-%m-%d')
                for item, amount in expenses:
                    c.execute("INSERT INTO transactions (user_id, type, amount, category, date) VALUES (?, ?, ?, ?, ?)",
                              (user_id, 'expense', amount, item, date))
                conn.commit()
                await update.message.reply_text(f"Xarajatlar saqlandi: {', '.join([f'{item}: {amount}' for item, amount in expenses])}")
                await show_balance(update, context)
        except sqlite3.Error as e:
            await update.message.reply_text(f"Ma'lumotlar bazasida xato yuz berdi: {e}")
    else:
        await update.message.reply_text("Iltimos, to‘g‘ri formatda kiriting: <kategoriya> <miqdor>\nMasalan: ovqat 100 yoki transport xarajatlari 500")

# Daromad qo‘shish
async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        args = context.args
        if not args:
            raise ValueError("Miqdor kiritilmadi")
        amount = int(args[0])
        category = ' '.join(args[1:]) or 'Umumiy'
        date = datetime.now().strftime('%Y-%m-%d')
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO transactions (user_id, type, amount, category, date) VALUES (?, ?, ?, ?, ?)",
                      (user_id, 'income', amount, category, date))
            conn.commit()
        await update.message.reply_text(f"Daromad saqlandi: {amount} ({category})")
        await show_balance(update, context)
    except (IndexError, ValueError) as e:
        await update.message.reply_text(f"Xato: {e}\nTo‘g‘ri format: /daromad <miqdor> <kategoriya>\nMasalan: /daromad 1000 ish haqi")

# Balansni ko‘rsatish
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    date = datetime.now().strftime('%Y-%m-%d')
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND date = ? GROUP BY type", (user_id, date))
            results = c.fetchall()

        income = 0
        expense = 0
        for t_type, amount in results:
            if t_type == 'income':
                income = amount or 0
            elif t_type == 'expense':
                expense = amount or 0

        balance = income - expense
        await update.effective_message.reply_text(f"Kunlik hisob:\nJami daromad: {income}\nJami xarajat: {expense}\nBalans: {balance}")
    except sqlite3.Error as e:
        await update.effective_message.reply_text(f"Ma'lumotlar bazasida xato: {e}")

# Xarajatlarni tahrirlash
async def edit_xarajat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        args = context.args
        if len(args) < 1:
            raise ValueError("Tranzaksiya ID kiritilmadi")
        transaction_id = int(args[0])
        new_amount = int(args[1]) if len(args) > 1 else None
        new_category = ' '.join(args[2:]) if len(args) > 2 else None

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM transactions WHERE id = ?", (transaction_id,))
            result = c.fetchone()

            if not result or result[0] != user_id:
                await update.message.reply_text("Bu tranzaksiya sizga tegishli emas yoki topilmadi!")
                return

            update_query = "UPDATE transactions SET"
            update_params = []
            if new_amount is not None:
                update_query += " amount = ?,"
                update_params.append(new_amount)
            if new_category is not None:
                update_query += " category = ?,"
                update_params.append(new_category)

            if not update_params:
                await update.message.reply_text("Hech qanday o‘zgartirish kiritilmadi!")
                return

            update_query = update_query.rstrip(',') + " WHERE id = ? AND user_id = ?"
            update_params.extend([transaction_id, user_id])

            c.execute(update_query, update_params)
            conn.commit()
        await update.message.reply_text("Xarajat muvaffaqiyatli tahrirlandi!")
        await show_balance(update, context)
    except (IndexError, ValueError) as e:
        await update.message.reply_text(f"Xato: {e}\nTo‘g‘ri format: /edit <tranzaksiya_id> <yangi_miqdor> <yangi_kategoriya>\nMasalan: /edit 1 200 yangi kategoriya")

# Statistika
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT type, SUM(amount), COUNT(*) FROM transactions WHERE user_id = ? GROUP BY type", (user_id,))
            results = c.fetchall()

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
    except sqlite3.Error as e:
        await update.message.reply_text(f"Ma'lumotlar bazasida xato: {e}")

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
    try:
        with get_db_connection() as conn:
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
                _, last_day = monthrange(today.year, today.month)
                end_date = today.replace(day=last_day).strftime('%Y-%m-%d')
                c.execute("SELECT type, amount, category, date FROM transactions WHERE user_id = ? AND date BETWEEN ? AND ?",
                          (user_id, start_date, end_date))

            transactions = c.fetchall()

        filename = f"{period}_report_{user_id}.pdf"
        c_pdf = canvas.Canvas(filename, pagesize=letter)
        c_pdf.setFont("Helvetica", 12)
        c_pdf.drawString(100, 750, f"{period.capitalize()} Hisobot")
        y = 700
        total_income = 0
        total_expense = 0
        for t_type, amount, category, date in transactions:
            if y < 50:  # Yangi sahifa ochish
                c_pdf.showPage()
                c_pdf.setFont("Helvetica", 12)
                y = 750
            c_pdf.drawString(100, y, f"{t_type.capitalize()}: {category} - {amount} ({date})")
            if t_type == 'income':
                total_income += amount
            else:
                total_expense += amount
            y -= 20
        c_pdf.drawString(100, y - 20, f"Jami daromad: {total_income}")
        c_pdf.drawString(100, y - 40, f"Jami xarajat: {total_expense}")
        c_pdf.drawString(100, y - 60, f"Balans: {total_income - total_expense}")
        c_pdf.save()
        return filename
    except Exception as e:
        print(f"PDF generatsiyasida xato: {e}")
        return None

async def process_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    period = update.callback_query.data.split('_')[0]

    if update.callback_query.data == 'total_balance':
        await show_balance(update.callback_query, context)
    else:
        filename = generate_pdf(user_id, period)
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'rb') as file:
                    await update.callback_query.message.reply_document(file, caption=f"{period.capitalize()} hisobot")
            finally:
                try:
                    os.remove(filename)
                except OSError as e:
                    print(f"Faylni o‘chirishda xato: {e}")
        else:
            await update.callback_query.message.reply_text("Hisobotni yaratishda xato yuz berdi.")
    await update.callback_query.answer()

# Guruh hisobi
async def group_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT user_id, SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income, "
                          "SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense "
                          "FROM transactions WHERE date = ? GROUP BY user_id",
                          (datetime.now().strftime('%Y-%m-%d'),))
                results = c.fetchall()

            response = "Guruh hisobi (bugun):\n"
            for user_id, income, expense in results:
                response += f"Foydalanuvchi {user_id}: Daromad: {income or 0}, Xarajat: {expense or 0}, Balans: {(income or 0) - (expense or 0)}\n"
            await update.message.reply_text(response or "Bugun hech qanday tranzaksiya yo‘q.")
        except sqlite3.Error as e:
            await update.message.reply_text(f"Ma'lumotlar bazasida xato: {e}")
    else:
        await update.message.reply_text("Bu buyruq faqat guruhlarda ishlaydi.")

# Kun yangilanishini tekshirish
async def check_new_day(context: ContextTypes.DEFAULT_TYPE):
    current_date = datetime.now().strftime('%Y-%m-%d')
    # Yangi kun boshlanganda maxsus logika qo‘shish mumkin
    pass

def main():
    try:
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
    except Exception as e:
        print(f"Botni ishga tushirishda xato: {e}")

if __name__ == '__main__':
    main()
