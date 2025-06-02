# Finance Bot

Finance Bot - bu Telegram orqali shaxsiy va guruhdagi moliyaviy hisob-kitoblarni boshqarishga yordam beradigan bot. Xarajatlar avtomatik saqlanadi, daromadlar va hisobotlar esa buyruqlar va inline tugmalar orqali boshqariladi. Har bir foydalanuvchining ma'lumotlari alohida saqlanadi va guruhlarda aralashmaydi.

## Xususiyatlar
- **Avtomatik xarajat kiritish**: Oddiy matn (masalan, `non 3000 suv 2000`) orqali xarajatlar avtomatik saqlanadi.
- **Daromad qo‘shish**: `/daromad <miqdor> <kategoriya>` orqali daromad kiritish.
- **Xarajatlarni tahrirlash**: `/edit <tranzaksiya_id> <yangi_miqdor> <yangi_kategoriya>` orqali xarajatlarni tahrirlash.
- **Statistika**: `/stats` orqali umumiy daromad, xarajat va balans.
- **PDF hisobotlar**: `/hisobot` orqali kunlik, haftalik va oylik PDF hisobotlar.
- **Jami hisob**: Har bir operatsiyadan so‘ng kunlik balans ko‘rsatiladi.
- **Guruh rejimi**: Har bir foydalanuvchining hisobi alohida, `/guruh_hisob` orqali umumiy statistika.
- **Maxfiylik**: Foydalanuvchilarning ma'lumotlari bir-biriga ko‘rinmaydi.

## O‘rnatish
1. **Repozitoriyani klonlash**:
   ```bash
   git clone https://github.com/yourusername/finance-bot.git
   cd finance-bot
