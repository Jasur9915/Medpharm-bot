# Medpharm-bot
Telegram harajat bot
PK     !�Z%�
  �
     bot.py
import telebot
from telebot import types
import json
from datetime import datetime
from fpdf import FPDF

TOKEN = "8116269873:AAEnl9QCBTFxT0xxySuKshd5lHIJ3Ybi1Lg"
bot = telebot.TeleBot(TOKEN)

data_file = 'data.json'

def load_data():
    try:
        with open(data_file, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)

def add_entry(user_id, text, is_income=False):
    data = load_data()
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')
    user_data = data.get(str(user_id), {})
    entries = user_data.get(date_str, [])
    amount, desc = parse_text(text)
    entries.append({
        "time": time_str,
        "desc": desc,
        "amount": amount,
        "type": "income" if is_income else "expense"
    })
    user_data[date_str] = entries
    data[str(user_id)] = user_data
    save_data(data)

def parse_text(text):
    parts = text.split()
    try:
        amount = int(parts[-1])
        desc = " ".join(parts[:-1])
        return amount, desc
    except:
        return 0, text

def generate_report(user_id):
    data = load_data()
    user_data = data.get(str(user_id), {})
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.image("logo.png", x=80, w=50)
    pdf.ln(20)
    pdf.cell(200, 10, txt="Hisobot (Medpharm)", ln=True, align='C')
    total_income = 0
    total_expense = 0

    for date, entries in sorted(user_data.items()):
        pdf.cell(200, 10, txt=f"Sana: {date}", ln=True)
        for e in entries:
            line = f"{e['time']} - {e['desc']} - {e['amount']} so'm [{e['type']}]"
            pdf.cell(200, 8, txt=line, ln=True)
            if e['type'] == 'income':
                total_income += e['amount']
            else:
                total_expense += e['amount']

    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Jami daromad: {total_income} so'm", ln=True)
    pdf.cell(200, 10, txt=f"Jami xarajat: {total_expense} so'm", ln=True)

    file_path = f"hisobot_{user_id}.pdf"
    pdf.output(file_path)
    return file_path

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Xarajat", "➕ Daromad")
    markup.add("📊 Hisobot (PDF)")
    bot.send_message(message.chat.id, "Medpharm hisob-kitob botiga xush kelibsiz!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 Hisobot (PDF)")
def send_report(message):
    file = generate_report(message.from_user.id)
    with open(file, 'rb') as f:
        bot.send_document(message.chat.id, f)

@bot.message_handler(func=lambda m: m.text == "➕ Xarajat")
def ask_expense(message):
    bot.send_message(message.chat.id, "Xarajatni kiriting (masalan: non 5000):")
    bot.register_next_step_handler(message, save_expense)

def save_expense(message):
    add_entry(message.from_user.id, message.text)
    bot.send_message(message.chat.id, "Xarajat saqlandi.")

@bot.message_handler(func=lambda m: m.text == "➕ Daromad")
def ask_income(message):
    bot.send_message(message.chat.id, "Daromadni kiriting (masalan: oylik 2000000):")
    bot.register_next_step_handler(message, save_income)

def save_income(message):
    add_entry(message.from_user.id, message.text, is_income=True)
    bot.send_message(message.chat.id, "Daromad saqlandi.")

bot.polling()
PK     !�ZC���      	   data.json{}PK     !�Z�pټ         requirements.txtpyTelegramBotAPI
fpdf
PK     !�Z�_���  �     logo.png�PNG


   
IHDR  ,   d   �c��  �IDATx����j�@@Q���9]�I�[�R=g58�����4M��Q� xw"��!&B��b"��!&B��b"��!&B��b"��!&B��b"��!&B��b"��!&B��b"��!&B��b"��!������b���[��I���Zo�=8p{�1�iڭq���������ew�v%���LxҼ^��Z\�ө�����9�ש��=�m����1���nӷ_?�j~�ۺ���2�f��gڙ̖S�m�W�ϘE����/�
4��S&!p���AL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL�!�D1BL��oo��
2p    IEND�B`�PK     !�Z%�
  �
             ��    bot.pyPK     !�ZC���      	           ���
  data.jsonPK     !�Z�pټ                 ���
  requirements.txtPK     !�Z�_���  �             ��  logo.pngPK      �   -    
