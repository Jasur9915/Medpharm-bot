import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import time

# Bot tokeni va Google Sheets sozlamalari
TOKEN = "YOUR_BOT_TOKEN"  # Telegram BotFather’dan oling
GOOGLE_SHEETS_CREDENTIALS = "YOUR_GOOGLE_SHEETS_JSON"  # Google Sheets JSON fayl nomi

# Ma'lumotlar bazasini yaratish
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (user_id INTEGER, category TEXT, amount REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS budgets
                 (user_id INTEGER, budget_type TEXT, amount REAL)''')
    conn.commit()
    conn.close()

# Google Sheets bilan ulanish
def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
    client = gspread.authorize(creds)
    return client.open("ExpenseBot").sheet1

# Harajat qo'shish
def add_expense(user_id, category, amount, date):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("INSERT INTO expenses (user_id, category, amount, date) VALUES (?, ?, ?, ?)",
              (user_id, category, amount, date))
    conn.commit()
    conn.close()
    
    # Google Sheets'ga yozish
    try:
        sheet = connect_to_google_sheets()
        sheet.append_row([str(user_id), category, amount, date])
    except Exception as e:
        print(f"Google Sheets xatosi: {e}")

# Budjet o'rnatish
def set_budget(user_id, budget_type, amount):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("REPLACE INTO budgets (user_id, budget_type, amount) VALUES (?, ?, ?)",
              (user_id, budget_type, amount))
    conn.commit()
    conn.close()

# Budjetni tekshirish
def check_budget(user_id, budget_type):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("SELECT amount FROM budgets WHERE user_id = ? AND budget_type = ?", (user_id, budget_type))
    budget = c.fetchone()
    if not budget:
        return None, 0
    budget_amount = budget[0]
    
    if budget_type == "weekly":
        start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_date = start_date + timedelta(days=6)
        c.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date BETWEEN ? AND ?",
                  (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    elif budget_type == "monthly":
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        c.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date >= ?",
                  (user_id, start_date))
    elif budget_type == "daily":
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date = ?",
                  (user_id, today))
    
    total_expense = c.fetchone()[0] or 0
    conn.close()
    return budget_amount, total_expense

# Valyuta konvertatsiyasi
def convert_currency(amount, to_currency="USD"):
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/UZS")
        rates = response.json()["rates"]
        return amount / rates[to_currency]
    except:
        return amount  # Agar API ishlamasa, xuddi shu summa qaytariladi

# Hisobot olish (kunlik, haftalik, oylik)
def get_report(user_id, report_type):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    
    if report_type == "daily":
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = ? AND date = ? GROUP BY category",
                  (user_id, today))
    elif report_type == "weekly":
        start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_date = start_date + timedelta(days=6)
        c.execute("SELECT category, SUM(amount), date FROM expenses WHERE user_id = ? AND date BETWEEN ? AND ? GROUP BY category, strftime('%W', date)",
                  (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    elif report_type == "monthly":
        c.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now') GROUP BY category",
                  (user_id,))
    
    data = c.fetchall()
    conn.close()
    return data

# PDF hisobot yaratish
def create_pdf_report(user_id, report_type, filename="report.pdf"):
    data = get_report(user_id, report_type)
    
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, f"{report_type.capitalize()} Harajatlar Hisoboti")
    y = 700
    total = 0
    for category, amount in data:
        c.drawString(120, y, f"{category}: {amount} so'm (USD: {convert_currency(amount):.2f})")
        total += amount
        y -= 20
    c.drawString(120, y, f"Umumiy: {total} so'm (USD: {convert_currency(total):.2f})")
    
    # Diagramma qo'shish
    plt.figure(figsize=(6, 4))
    categories, amounts = zip(*data) if data else ([], [])
    if categories:
        plt.pie(amounts, labels=categories, autopct='%1.1f%%')
        plt.savefig("chart.png")
        plt.close()
        c.drawImage("chart.png", 100, y-200, width=200, height=150)
        os.remove("chart.png")
    
    c.save()

# Eslatma yuborish
async def reminder_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(job.context, text="Bugungi harajatlaringizni kiritdingizmi?")

# Start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Harajat botga xush kelibsiz.\n"
        "Harajat kiritish: Kategoriya: Summa: Sana (Misol: Oziq-ovqat: 50000: 2025-06-04)\n"
        "Hisobotlar: /hisobot kunlik | haftalik | oylik\n"
        "Budjet: /budjet haftalik 500000\n"
        "Eslatma: /eslatma 20:00\n"
        "Valyuta: /valyuta USD"
    )

# Harajat kiritish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    try:
        category, amount, *date = text.split(":")
        amount = float(amount.strip())
        date = date[0].strip() if date else datetime.now().strftime('%Y-%m-%d')
        add_expense(user_id, category.strip(), amount, date)
        await update.message.reply_text(f"Harajat qo'shildi: {category}, {amount} so'm, {date}")

        # Budjetni tekshirish
        for budget_type in ["daily", "weekly", "monthly"]:
            budget, total_expense = check_budget(user_id, budget_type)
            if budget and total_expense >= budget * 0.8:
                await update.message.reply_text(f"Ehtiyot! {budget_type.capitalize()} budjetingizdan 80% foydalandingiz!")
    except Exception as e:
        await update.message.reply_text("Xato format. Misol: Oziq-ovqat: 50000: 2025-06-04")

# Hisobot buyrug'i
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        report_type = context.args[0].lower()
        if report_type not in ["daily", "weekly", "monthly"]:
            raise ValueError
        filename = f"{report_type}_report.pdf"
        create_pdf_report(user_id, report_type, filename)
        await update.message.reply_document(document=open(filename, "rb"))
        os.remove(filename)
    except:
        await update.message.reply_text("Xato. Misol: /hisobot kunlik | haftalik | oylik")

# Budjet o'rnatish
async def set_budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        budget_type, amount = context.args
        amount = float(amount)
        set_budget(user_id, budget_type.lower(), amount)
        await update.message.reply_text(f"{budget_type.capitalize()} budjet o'rnatildi: {amount} so'm")
    except:
        await update.message.reply_text("Xato format. Misol: /budjet haftalik 500000")

# Eslatma sozlash
async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        _, time_str = update.message.text.split()
        hour, minute = map(int, time_str.split(":"))
        context.job_queue.run_daily(reminder_callback, time(hour=hour, minute=minute), context=user_id)
        await update.message.reply_text(f"Eslatma sozlandi: Har kuni {time_str} da eslataman.")
    except:
        await update.message.reply_text("Xato format. Misol: /eslatma 20:00")

# Valyuta konvertatsiyasi
async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        to_currency = context.args[0].upper()
        data = get_report(user_id, "monthly")
        total = sum(amount for _, amount in data)
        converted = convert_currency(total, to_currency)
        await update.message.reply_text(f"Joriy oyning umumiy harajati: {total} so'm ({converted:.2f} {to_currency})")
    except:
        await update.message.reply_text("Xato format. Misol: /valyuta USD")

# Asosiy funksiya
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hisobot", report))
    app.add_handler(CommandHandler("budjet", set_budget_command))
    app.add_handler(CommandHandler("eslatma", set_reminder))
    app.add_handler(CommandHandler("valyuta", convert))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
