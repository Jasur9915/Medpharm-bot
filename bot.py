import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from datetime import datetime
from utils.parser import parse_entry
from utils.storage import add_entry, get_user_report, delete_last_entry
from utils.pdf_report import generate_pdf

BOT_TOKEN = os.environ["BOT_TOKEN"]
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(commands=["start"])
async def start_handler(message: Message):
    await message.answer(
        "👋 Salom! Medpharm Botga xush kelibsiz.\n"
        "'Narsa 25 dona' deb yozing — bot avtomatik tanib oladi.\n"
        "'hisobot' deb yozsangiz, hisobot olasiz.\n"
        "'bekor' deb yozsangiz, oxirgi yozuv o‘chiriladi."
    )

@dp.message(lambda m: m.text.lower() == 'hisobot')
async def report_handler(message: Message):
    entries = get_user_report(message.from_user.id)
    if not entries:
        await message.answer("📭 Sizda hali yozuvlar yo‘q.")
    else:
        pdf_path = generate_pdf(message.from_user.full_name, entries)
        with open(pdf_path, "rb") as pdf:
            await message.answer_document(pdf)

@dp.message(lambda m: m.text.lower() == 'bekor')
async def delete_handler(message: Message):
    success = delete_last_entry(message.from_user.id)
    if success:
        await message.answer("✅ Oxirgi yozuv o‘chirildi.")
    else:
        await message.answer("⚠️ O‘chirish uchun yozuv topilmadi.")

@dp.message()
async def data_handler(message: Message):
    parsed = parse_entry(message.text)
    if parsed:
        entry = {
            "user_id": message.from_user.id,
            "username": message.from_user.username or message.from_user.full_name,
            "item": parsed["item"],
            "amount": parsed["amount"],
            "unit": parsed["unit"],
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        add_entry(entry)
        await message.answer(f"✅ Yozildi: {entry['item']} – {entry['amount']} {entry['unit']}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
