import re
import json
from datetime import datetime
from collections import defaultdict

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_entries(text):
    text = text.replace("\n", " ").lower()
    name_match = re.search(r"(\w+\s+opaga|akamga|xonaga)?", text)
    location_match = re.search(r"(\w+ga|\w+da)", text)
    name = name_match.group().strip() if name_match else ""
    location = location_match.group().strip() if location_match else ""

    entries = []
    matches = re.findall(r"([\w’']+)[\s:,-]+(\d+(?:[.,]\d+)?)", text)
    for match in matches:
        item = match[0]
        try:
            amount = float(match[1].replace(",", "."))
        except:
            continue
        unit = "dona"
        category = "Dori"
        entries.append({
            "item": item.capitalize(),
            "amount": amount,
            "unit": unit,
            "category": category,
            "name": name,
            "location": location,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    return entries

def save_entry(user, entry):
    data = load_data()
    uid = str(user.id)
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    if uid not in data:
        data[uid] = {"name": full_name, "entries": []}
    data[uid]["entries"].append(entry)
    save_data(data)
