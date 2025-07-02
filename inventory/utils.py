# inventory/utils.py

import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from .models import InventoryItem

def export_inventory_pdf():
    """
    Generate and return a PDF summary of all inventory items.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 14)
    p.drawString(2 * cm, height - 2 * cm, "Inventory Report")

    p.setFont("Helvetica", 10)
    y = height - 3 * cm
    row_height = 1 * cm
    p.drawString(2 * cm, y, "Product")
    p.drawString(7 * cm, y, "Warehouse")
    p.drawString(12 * cm, y, "Quantity")
    p.drawString(15 * cm, y, "Low Stock?")
    y -= row_height

    for item in InventoryItem.objects.select_related('product', 'warehouse', 'variant', 'supplier'):
        if y < 2 * cm:
            p.showPage()
            y = height - 2 * cm

        variant_info = f" ({item.variant.size}/{item.variant.weight})" if item.variant else ""
        p.drawString(2 * cm, y, item.product.name + variant_info)
        p.drawString(7 * cm, y, item.warehouse.name)
        p.drawString(12 * cm, y, str(item.quantity))
        p.drawString(15 * cm, y, "Yes" if item.is_low_stock else "No")
        y -= row_height

    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='inventory_report.pdf')
