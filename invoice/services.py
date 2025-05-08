# invoice/services.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from django.core.files import File
from django.conf import settings
import os


def generate_invoice_pdf(invoice):
    """Generate PDF invoice using ReportLab"""
    buffer = BytesIO()

    # Create the PDF object
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Set up styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=1,  # Center aligned
        spaceAfter=20
    )

    # Add title
    title = Paragraph(f"Invoice #{invoice.invoice_number}", title_style)
    title.wrapOn(p, width - 100, height)
    title.drawOn(p, 50, height - 50)

    # Add invoice details
    details = [
        ['Issued Date:', invoice.issued_date.strftime('%B %d, %Y')],
        ['Due Date:', invoice.due_date.strftime('%B %d, %Y')],
        ['Status:', invoice.get_status_display()],
        ['Payment Terms:', invoice.get_payment_terms_display()],
    ]

    details_table = Table(details, colWidths=[150, 200])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    details_table.wrapOn(p, width - 100, height)
    details_table.drawOn(p, 50, height - 120)

    # Add line items table
    line_items = [['Description', 'Qty', 'Unit Price', 'Tax', 'Total']]
    for item in invoice.line_items.all():
        line_items.append([
            item.product_name,
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"{item.tax_rate}%",
            f"${item.total_price:.2f}"
        ])

    items_table = Table(line_items, colWidths=[250, 50, 80, 50, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    items_table.wrapOn(p, width - 100, height)
    items_table.drawOn(p, 50, height - 300)

    # Add totals
    totals = [
        ['Subtotal:', f"${invoice.subtotal:.2f}"],
        ['Tax:', f"${invoice.tax_amount:.2f}"],
        ['Shipping:', f"${invoice.shipping_charge:.2f}"],
        ['Discount:', f"-${invoice.discount_amount:.2f}"],
        ['Total:', f"${invoice.total_amount:.2f}"],
        ['Amount Paid:', f"${invoice.amount_paid:.2f}"],
        ['Balance Due:', f"${invoice.balance_due:.2f}"],
    ]

    totals_table = Table(totals, colWidths=[150, 100])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))
    totals_table.wrapOn(p, width - 100, height)
    totals_table.drawOn(p, width - 250, height - 450)

    # Add notes and terms
    if invoice.notes:
        p.drawString(50, 200, "Notes:")
        p.drawString(50, 185, invoice.notes)

    if invoice.terms_conditions:
        p.drawString(50, 150, "Terms & Conditions:")
        p.drawString(50, 135, invoice.terms_conditions)

    # Close the PDF object cleanly
    p.showPage()
    p.save()

    # Get PDF content
    buffer.seek(0)

    # Save to file
    filename = f"{invoice.invoice_number}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'wb') as f:
        f.write(buffer.read())

    # Save to invoice model
    invoice.pdf_file.save(filename, File(open(filepath, 'rb')))
    invoice.save()

    return filepath