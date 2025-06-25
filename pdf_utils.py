from fpdf import FPDF
from utils import load_data
from datetime import datetime, timedelta

def generate_weekly_pdf(file_path="weekly_report.pdf"):
    data = load_data()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="📊 Haftalik Hisobot", ln=True, align="C")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    for uid, user_data in data.items():
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt=f"👤 {user_data['name']}:", ln=True)
        pdf.set_font("Arial", "", 12)
        for e in user_data["entries"]:
            if e["date"] >= start_date:
                row = f"{e['date']} – {e['item']} {e['amount']} {e['unit']} ({e['category']})"
                if e.get("name"): row += f", 👥 {e['name']}"
                if e.get("location"): row += f", 📍 {e['location']}"
                pdf.cell(200, 10, txt=row, ln=True)

    pdf.output(file_path)
    return file_path
