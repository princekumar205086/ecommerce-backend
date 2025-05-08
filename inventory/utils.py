# inventory/utils.py
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from .models import InventoryItem

def export_inventory_pdf():
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    p.drawString(100, 800, "Inventory Report")
    y = 760
    for item in InventoryItem.objects.all():
        line = f"{item.product.name} in {item.warehouse.name}: {item.quantity}"
        p.drawString(100, y, line)
        y -= 20
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='inventory_report.pdf')