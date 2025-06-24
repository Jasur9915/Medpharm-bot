import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from utils import parse_entry, save_data, load_data, generate_pdf
import os
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

data = load_data()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Salom! Xarajatlaringizni menga yozing:\nMisol: `Orasta opaga Laktorin 30`\nYoki: `Yana 5 dona`")

@dp.message()
async def handle_entry(message: Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    parsed = parse_entry(message.text, user_id)

    if parsed:
        data.setdefault(chat_id, {}).setdefault(user_id, []).append(parsed)
        save_data(data)
        await message.reply(f"✅ Yozildi: {parsed['name']} - {parsed['amount']} {parsed['unit']} ({parsed['place']})")
    elif message.text.lower().startswith("hisobot"):
        pdf = generate_pdf(data.get(chat_id, {}), chat_id)
        await message.reply_document(types.BufferedInputFile(pdf, filename="hisobot.pdf"))
    else:
        await message.reply("⚠️ Iltimos, to‘g‘ri formatda yozing. Masalan: `Orasta opaga Laktorin 30` yoki `Yana 5 dona`")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
