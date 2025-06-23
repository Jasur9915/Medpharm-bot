main.py

import os import logging import asyncio from datetime import datetime from aiogram import Bot, Dispatcher, types from aiogram.enums import ParseMode from aiogram.types import Message

BOT_TOKEN = os.environ.get("BOT_TOKEN") logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML) dp = Dispatcher()

🧠 Oddiy parser funksiyasi (Narsa + raqam + birlik)

def parse_entry(text): parts = text.split() if len(parts) >= 2 and parts[-2].isdigit(): return { "item": " ".join(parts[:-2]), "amount": int(parts[-2]), "unit": parts[-1] } return None

🧠 Foydalanuvchi ma'lumotlarini saqlovchi vaqtinchalik ombor (RAM)

user_data = {}

/start komandasi

@dp.message(commands=["start"]) async def start_handler(message: Message): await message.answer( "👋 Salom! Medpharm Botga xush kelibsiz.\n" "Misol: <b>Dori 25 dona</b> deb yozing.\n" "<b>hisobot</b> deb yozsangiz, yozgan narsalaringiz chiqadi.\n" "<b>bekor</b> deb yozsangiz, oxirgi yozuv o‘chiriladi." )

hisobot komandasi

@dp.message(lambda m: m.text.lower() == "hisobot") async def report_handler(message: Message): uid = message.from_user.id entries = user_data.get(uid, []) if not entries: await message.answer("📭 Sizda yozuvlar yo‘q.") else: text = "\n".join([ f"{e['date']}: {e['item']} – {e['amount']} {e['unit']}" for e in entries ]) await message.answer(f"📋 Sizning yozuvlaringiz:\n{text}")

bekor komandasi

@dp.message(lambda m: m.text.lower() == "bekor") async def delete_last(message: Message): uid = message.from_user.id if user_data.get(uid): user_data[uid].pop() await message.answer("✅ Oxirgi yozuv o‘chirildi.") else: await message.answer("⚠️ O‘chirish uchun yozuv topilmadi.")

Matnli yozuvlar

@dp.message() async def entry_handler(message: Message): parsed = parse_entry(message.text) if parsed: uid = message.from_user.id entry = { "item": parsed["item"], "amount": parsed["amount"], "unit": parsed["unit"], "date": datetime.now().strftime("%Y-%m-%d") } user_data.setdefault(uid, []).append(entry) await message.answer(f"✅ Yozildi: {entry['item']} – {entry['amount']} {entry['unit']}")

async def main(): await dp.start_polling(bot)

if name == "main": asyncio.run(main())

