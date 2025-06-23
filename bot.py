medpharm-bot/main.py

import os import logging from aiogram import Bot, Dispatcher, executor, types from datetime import datetime from utils.parser import parse_entry from utils.storage import add_entry, get_user_report, delete_last_entry from utils.pdf_report import generate_pdf

BOT_TOKEN = os.environ["BOT_TOKEN"] logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN) dp = Dispatcher(bot)

@dp.message_handler(commands=['start']) async def start_handler(message: types.Message): await message.reply("👋 Salom! Medpharm Botga xush kelibsiz. 'Narsa 25 dona' deb yozing — bot avtomatik tanib oladi. 'hisobot' deb yozsangiz, hisobot olasiz. 'bekor' deb yozsangiz, oxirgi yozuv o‘chiriladi.")

@dp.message_handler(lambda m: m.text.lower() == 'hisobot') async def report_handler(message: types.Message): entries = get_user_report(message.from_user.id) if not entries: await message.reply("📭 Sizda hali yozuvlar yo‘q.") else: pdf_path = generate_pdf(message.from_user.full_name, entries) with open(pdf_path, "rb") as pdf: await message.reply_document(pdf)

@dp.message_handler(lambda m: m.text.lower() == 'bekor') async def delete_handler(message: types.Message): success = delete_last_entry(message.from_user.id) if success: await message.reply("✅ Oxirgi yozuv o‘chirildi.") else: await message.reply("⚠️ O‘chirish uchun yozuv topilmadi.")

@dp.message_handler() async def data_handler(message: types.Message): parsed = parse_entry(message.text) if parsed: entry = { "user_id": message.from_user.id, "username": message.from_user.username or message.from_user.full_name, "item": parsed["item"], "amount": parsed["amount"], "unit": parsed["unit"], "date": datetime.now().strftime("%Y-%m-%d") } add_entry(entry) await message.reply(f"✅ Yozildi: {entry['item']} – {entry['amount']} {entry['unit']}") else: pass

if name == 'main': executor.start_polling(dp, skip_updates=True)

medpharm-bot/utils/parser.py

def parse_entry(text): import re pattern = r"(?P<item>\w[\w\s])\s+(?P<amount>\d+[.,]?\d)\s*(?P<unit>\w+)?" match = re.match(pattern, text.strip()) if match: return { "item": match.group("item").strip(), "amount": float(match.group("amount").replace(',', '.')), "unit": match.group("unit") or "" } return None

medpharm-bot/utils/storage.py

entries_by_user = {}

def add_entry(entry): user_id = entry["user_id"] if user_id not in entries_by_user: entries_by_user[user_id] = [] entries_by_user[user_id].append(entry)

def get_user_report(user_id): return entries_by_user.get(user_id, [])

def delete_last_entry(user_id): if user_id in entries_by_user and entries_by_user[user_id]: entries_by_user[user_id].pop() return True return False

medpharm-bot/utils/pdf_report.py

from fpdf import FPDF from datetime import datetime import os

def generate_pdf(username, entries): filename = f"{username.replace(' ', '_')}_hisobot.pdf" pdf = FPDF() pdf.add_page() pdf.set_font("Arial", size=12)

pdf.set_text_color(0)
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt="Medpharm xisoboti", ln=True, align='C')
pdf.ln(10)

current_date = datetime.now().strftime("%Y-%m-%d")
pdf.set_font("Arial", size=11)
pdf.cell(200, 10, txt=f"Sana: {current_date}", ln=True)
pdf.cell(200, 10, txt=f"Foydalanuvchi: {username}", ln=True)
pdf.ln(5)

for entry in entries:
    line = f"{entry['date']} - {entry['item']} – {entry['amount']} {entry['unit']}"
    pdf.cell(200, 8, txt=line, ln=True)

pdf.output(filename)
return filename

medpharm-bot/requirements.txt

aiogram fpdf

medpharm-bot/Procfile

web: python main.py

medpharm-bot/.env.example

BOT_TOKEN=your_bot_token_here

medpharm-bot/README.md

Medpharm Telegram Bot

Telegram orqali har kim o‘z harajatlarini yoki ma'lumotlarini kiritib boradi. Bot har bir foydalanuvchining yozuvlarini alohida saqlaydi va hisobotlarni chiqaradi.

✨ Xususiyatlar

Guruh va shaxsiy chatda ishlaydi

"Narsa 25 birlik" formatida yozuvlarni tanib oladi

Har bir foydalanuvchining yozuvlari alohida saqlanadi

hisobot deb yozsangiz, PDF hisobot beradi

bekor deb yozsangiz, oxirgi yozuvni o‘chiradi


🚀 Ishga tushirish (Render uchun)

1. GitHub repo yarating va bu fayllarni yuklang


2. Render.com saytida yangi Web Service yarating


3. Environment Variable ga quyidagini qo‘shing:

BOT_TOKEN = Sizning tokeningiz



4. Start Command avtomatik aniqlanadi: python main.py


5. Deploy qiling va bot ishlay boshlaydi ✅



🤖 Format misollari:

Olma 5 dona
Dori 12
Naqd 50000 so‘m

📄 PDF Hisobot

Har foydalanuvchining o‘ziga tegishli yozuvlar ko‘rsatiladi

Foydalanuvchi ismi va sana bilan chiqariladi



---

By Medpharm

