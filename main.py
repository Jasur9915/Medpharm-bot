import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime
from utils.parser import parse_entry
from utils.storage import add_entry, get_user_report, delete_last_entry
from utils.pdf_report import generate_pdf

BOT_TOKEN = os.environ["BOT_TOKEN"]
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply(
        "👋 Salom! Medpharm Botga xush kelibsiz.\n"
        "'Narsa 25 dona' deb yozing — bot avtomatik tanib oladi.\n"
        "'hisobot' deb yozsangiz, hisobot olasiz.\n"
        "'bekor' deb yozsangiz, oxirgi yozuv o‘chiriladi."
    )

@dp.message_handler(lambda m: m.text.lower() == 'hisobot')
async def report_handler(message: types.Message):
    entries = get_user_report(message.from_user.id)
    if not entries:
        await message.reply("📭 Sizda hali yozuvlar yo‘q.")
    else:
        pdf_path = generate_pdf(message.from_user.full_name, entries)
        with open(pdf_path, "rb") as pdf:
            await message.reply_document(pdf)

@dp.message_handler(lambda m: m.text.lower() == 'bekor')
async def delete_handler(message: types.Message):
    success = delete_last_entry(message.from_user.id)
    if success:
        await message.reply("✅ Oxirgi yozuv o‘chirildi.")
    else:
        await message.reply("⚠️ O‘chirish uchun yozuv topilmadi.")

@dp.message_handler()
async def data_handler(message: types.Message):
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
        await message.reply(f"✅ Yozildi: {entry['item']} – {entry['amount']} {entry['unit']}")
    else:
        pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
