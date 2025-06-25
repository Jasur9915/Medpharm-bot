from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from parser import parse_entry
from storage import add_entry, get_summary, generate_user_report
from pdf_utils import create_pdf
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)

@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer(f"👋 Salom, {msg.from_user.full_name}! Xarajatlarni yozing: masalan: <b>Laktorin 30</b> yoki <b>Orasta opaga Vitakom 20</b>")

@dp.message(Command("pdf"))
async def handle_pdf(msg: Message):
    pdf_path = create_pdf(msg.from_user.id)
    await msg.answer_document(types.FSInputFile(pdf_path))

@dp.message(Command("stat"))
async def handle_stats(msg: Message):
    summary = get_summary(msg.from_user.id)
    await msg.answer(summary)

@dp.message()
async def handle_entry(msg: Message):
    user_id = msg.from_user.id
    full_name = msg.from_user.full_name
    text = msg.text

    data = parse_entry(text)
    if not data:
        await msg.answer("⚠️ Hech narsa topilmadi. Masalan: <i>Laktorin 30</i> yoki <i>Qoqonga Orasta opaga Loramor 20</i>")
        return

    result = add_entry(user_id, full_name, data)
    await msg.answer(f"✅ Saqlandi: {result}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
