from reportlab.pdfgen import canvas
from datetime import datetime

def generate_pdf(filename='report.pdf', content='Hisobot'):
    c = canvas.Canvas(filename)
    c.drawString(100, 800, f"Hisobot: {datetime.now().strftime('%Y-%m-%d')}")
    c.drawString(100, 780, content)
    c.save()
