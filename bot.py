import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils.markdown import hbold
import asyncio
from dotenv import load_dotenv
from utils import parse_entries, save_entry
from pdf_utils import generate_weekly_pdf

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

@dp.message()
async def handle_message(message: Message):
    user = message.from_user
    parsed_entries = parse_entries(message.text)
    if parsed_entries:
        responses = []
        for entry in parsed_entries:
            save_entry(user, entry)
            responses.append(f"✅ {hbold(entry['item'])} – {entry['amount']} {entry['unit']} ({entry['category']})")
        await message.answer("\n".join(responses))
    else:
        await message.answer("⚠️ Format noto‘g‘ri. Masalan: Vitakom 20 yoki 'Orasta opaga Qoqonga Laktorin 30'")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
