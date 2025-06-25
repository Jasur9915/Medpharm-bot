import re

def parse_entry(text):
    pattern = re.findall(r'([A-ZА-Яa-zа-я0-9\-]+)\s*([\d.,]+)?\s*(kg|g|ml|so‘m|s|dona|ta|suv)?', text, re.IGNORECASE)
    result = []

    for name, amount, unit in pattern:
        if not name:
            continue
        try:
            amount = float(amount.replace(",", ".")) if amount else 1
        except:
            amount = 1
        unit = unit if unit else ""
        result.append({
            "name": name.lower(),
            "amount": amount,
            "unit": unit.lower()
        })
    return result
