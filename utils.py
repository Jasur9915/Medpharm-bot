
import re
import json
from datetime import datetime
from pdf_utils import create_pdf
from collections import defaultdict

DB_FILE = "data.json"
last_entry = {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def parse_entry(text, user_id):
    match = re.search(r"(.*?)(?:\s+(opaga|akamga|ukamga|Qoqonga|Qarshiga|Buxoroga))?\s*([\w\s]+)?\s*(\d+(?:[.,]\d+)?)\s*(\w+)?", text)
    if match:
        name = (match.group(3) or "").strip().title()
        amount = float(match.group(4).replace(",", "."))
        unit = match.group(5) or "dona"
        place = (match.group(2) or "Noma'lum").capitalize()
        if name:
            last_entry[user_id] = {"name": name, "unit": unit, "place": place}
        elif user_id in last_entry:
            name = last_entry[user_id]["name"]
            unit = unit or last_entry[user_id]["unit"]
            place = last_entry[user_id]["place"]
        else:
            return None
        return {
            "name": name,
            "amount": amount,
            "unit": unit,
            "place": place,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    return None

def generate_pdf(user_entries, chat_id):
    entries = []
    for uid, records in user_entries.items():
        for record in records:
            entries.append({
                "user": uid,
                **record
            })
    return create_pdf(entries, chat_id)
