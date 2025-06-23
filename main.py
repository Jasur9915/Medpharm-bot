import os
import logging
import asyncio
from datetime import datetime
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from fpdf import FPDF
import re

BOT_TOKEN = os.environ.get("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

user_data = defaultdict(list)

CATEGORY_KEYWORDS = {
    "Oziq-ovqat": ["non", "shakar", "tuxum", "go‘sht", "tovuq", "guruch"],
    "Buyum": ["kitob", "printer", "karopka", "karton", "qog'oz"],
    "Pul": ["so'm", "dollar", "ming", "million"]
}

def detect_category(item):
    text = item.lower()
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(w in text for w in words):
            return cat
    return "Boshqa"

def parse_entry(text):
    match = re.search(r"(.+?)\\s+(\\d+(?:[.,]\\d+)?)\\s*(\\w+)?$", text)
    if match:
        item = match.group(1).strip()
        amount = float(match.group(2).replace(",", "."))
        unit = match.group(3) or "dona"
        return {"item": item, "amount": amount, "unit": unit, "category": detect_category(item)}
    return None

def generate_pdf(name, entries):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Medpharm Hisobot - {name}", ln=True, align="C")
    pdf.ln(10)
    categories = defaultdict(list)
    for e in entries:
        categories[e['category']].append(e)
    for cat, items in categories.items():
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"[{cat}]", ln=True)
        pdf.set_font("Arial", size=12)
        for entry in items:
            line = f"{entry['date']} — {entry['item']} — {entry['amount']} {entry['unit']}"
            pdf.cell(200, 10, txt=line, ln=True)
        pdf.ln(5)
    path = f"report_{name.replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

@dp.message(commands=["start"])
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 PDF Hisobot", callback_data="pdf")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stat")]
    ])
    await message.answer(
        "👋 Salom! Medpharm Botga xush kelibsiz.\n"
        "Istalgan yozuvni yuboring: <b>Shakar 3.5 kg</b> yoki <b>Kitob 1 dona</b>.\n"
        "Yoki <b>hisobot</b> deb yozing.", reply_markup=keyboard
    )

@dp.callback_query(F.data == "pdf")
async def callback_pdf(call: types.CallbackQuery):
    uid = call.from_user.id
    name = call.from_user.full_name
    entries = user_data[uid]
    if not entries:
        await call.message.answer("📭 Sizda yozuvlar yo‘q.")
    else:
        pdf_path = generate_pdf(name, entries)
        await call.message.answer_document(FSInputFile(pdf_path))

@dp.callback_query(F.data == "stat")
async def callback_stat(call: types.CallbackQuery):
    uid = call.from_user.id
    entries = user_data[uid]
    if not entries:
        await call.message.answer("📭 Hali yozuv yo‘q.")
    else:
        stats = defaultdict(float)
        for e in entries:
            stats[e['category']] += e['amount']
        summary = "\\n".join([f"{k}: {v}" for k, v in stats.items()])
        await call.message.answer(f"📊 Statistika:\\n{summary}")

@dp.message(lambda m: m.text.lower() == "hisobot")
async def report_handler(message: types.Message):
    uid = message.from_user.id
    entries = user_data[uid]
    if not entries:
        await message.answer("📭 Sizda yozuvlar yo‘q.")
    else:
        text = "\\n".join([
            f"{e['date']}: {e['item']} – {e['amount']} {e['unit']} ({e['category']})"
            for e in entries
        ])
        await message.answer(f"📋 Sizning yozuvlaringiz:\\n{text}")

@dp.message(lambda m: m.text.lower() == "bekor")
async def delete_last(message: types.Message):
    uid = message.from_user.id
    if user_data[uid]:
        user_data[uid].pop()
        await message.answer("✅ Oxirgi yozuv o‘chirildi.")
    else:
        await message.answer("⚠️ O‘chirish uchun yozuv topilmadi.")

@dp.message()
async def entry_handler(message: types.Message):
    parsed = parse_entry(message.text)
    if parsed:
        uid = message.from_user.id
        entry = {
            "item": parsed["item"].capitalize(),
            "amount": parsed["amount"],
            "unit": parsed["unit"],
            "category": parsed["category"],
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        user_data[uid].append(entry)
        await message.answer(f"✅ Yozildi: {entry['item']} – {entry['amount']} {entry['unit']} ({entry['category']})")
    else:
        await message.answer("⚠️ Format noto‘g‘ri. Misol: <b>Karton 20 dona</b> yoki <b>Go‘sht 3 kg</b>")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
