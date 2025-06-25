def format_expense(text):
    try:
        name, amount = text.rsplit(' ', 1)
        return f"{name.strip().title()} – {int(amount):,} so'm"
    except Exception:
        return "Xatolik! Format: Narsa 10000"
