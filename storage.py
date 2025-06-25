import json
from collections import defaultdict
from datetime import datetime

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_entry(user_id, name, entries):
    data = load_data()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    if uid not in data:
        data[uid] = {}

    if today not in data[uid]:
        data[uid][today] = []

    for entry in entries:
        data[uid][today].append(entry)

    save_data(data)
    return ", ".join([f"{e['name']} {e['amount']} {e['unit']}" for e in entries])

def get_summary(user_id):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        return "📦 Ma’lumot yo‘q"

    all_items = defaultdict(float)
    for day in data[uid]:
        for entry in data[uid][day]:
            key = f"{entry['name']} {entry['unit']}"
            all_items[key] += entry['amount']

    result = "\n".join([f"{name}: {round(amount, 2)}" for name, amount in all_items.items()])
    return f"📊 Umumiy statistika:\n{result}"
