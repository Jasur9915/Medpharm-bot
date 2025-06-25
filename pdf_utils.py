from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from storage import load_data
from datetime import datetime

def create_pdf(user_id):
    data = load_data()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"report_{uid}.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica", 12)
    y = 800
    c.drawString(50, y, f"📄 Hisobot: {today}")
    y -= 30

    if uid not in data:
        c.drawString(50, y, "Ma’lumot topilmadi.")
    else:
        for date, entries in data[uid].items():
            c.drawString(50, y, f"📅 {date}")
            y -= 20
            for e in entries:
                line = f"• {e['name']} - {e['amount']} {e['unit']}"
                c.drawString(70, y, line)
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 800
    c.save()
    return filename
