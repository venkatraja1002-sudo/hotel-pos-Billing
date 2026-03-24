from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def make_invoice_pdf(restaurant_name, invoice_no, table_no, waiter_name, payment_method, cart_df, subtotal, tax_amount, total):
    """
    cart_df columns: Item, Qty, Price, Tax%, Amount
    returns bytes
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    left = 18 * mm
    right = w - 18 * mm
    y = h - 18 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, y, restaurant_name)
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    c.drawString(left, y, f"Invoice No: {invoice_no}")
    c.drawRightString(right, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 6 * mm

    c.drawString(left, y, f"Table: {table_no}")
    c.drawRightString(right, y, f"Waiter: {waiter_name}")
    y -= 6 * mm

    c.drawString(left, y, f"Payment: {payment_method}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, y, "Item")
    c.drawRightString(right - 80, y, "Qty")
    c.drawRightString(right - 50, y, "Price")
    c.drawRightString(right - 20, y, "Tax%")
    c.drawRightString(right, y, "Amount")
    y -= 4 * mm
    c.line(left, y, right, y)
    y -= 7 * mm

    c.setFont("Helvetica", 10)
    for _, r in cart_df.iterrows():
        item = str(r["Item"])
        if len(item) > 34:
            item = item[:34] + "..."
        c.drawString(left, y, item)
        c.drawRightString(right - 80, y, str(int(r["Qty"])))
        c.drawRightString(right - 50, y, f"{float(r['Price']):.2f}")
        c.drawRightString(right - 20, y, f"{float(r['Tax%']):.1f}")
        c.drawRightString(right, y, f"{float(r['Amount']):.2f}")
        y -= 6 * mm

        if y < 25 * mm:
            c.showPage()
            y = h - 18 * mm
            c.setFont("Helvetica", 10)

    y -= 2 * mm
    c.line(left, y, right, y)
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(right, y, f"Subtotal: ₹{subtotal:.2f}")
    y -= 6 * mm
    c.drawRightString(right, y, f"Tax: ₹{tax_amount:.2f}")
    y -= 7 * mm

    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(right, y, f"TOTAL: ₹{total:.2f}")
    y -= 12 * mm

    c.setFont("Helvetica", 9)
    c.drawString(left, y, "Thank you! Visit again.")

    c.showPage()
    c.save()
    data = buffer.getvalue()
    buffer.close()
    return data