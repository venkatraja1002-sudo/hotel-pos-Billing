import uuid
import pandas as pd
from db import get_conn

def add_menu_item(name, category, price, cost=0.0, tax_percent=0.0, available=1, image_bytes=None, image_mime=None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO menu_items (name, category, price, cost, tax_percent, available, image_blob, image_mime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, category, price, cost, tax_percent, available, image_bytes, image_mime))
    conn.commit()
    conn.close()

def update_menu_item(item_id, name, category, price, cost, tax_percent, available, image_bytes=None, image_mime=None, keep_old_image=True):
    conn = get_conn()
    cur = conn.cursor()

    if keep_old_image or image_bytes is None:
        cur.execute("""
            UPDATE menu_items
            SET name=?, category=?, price=?, cost=?, tax_percent=?, available=?
            WHERE item_id=?
        """, (name, category, price, cost, tax_percent, available, item_id))
    else:
        cur.execute("""
            UPDATE menu_items
            SET name=?, category=?, price=?, cost=?, tax_percent=?, available=?, image_blob=?, image_mime=?
            WHERE item_id=?
        """, (name, category, price, cost, tax_percent, available, image_bytes, image_mime, item_id))

    conn.commit()
    conn.close()

def delete_menu_item(item_id):
    conn = get_conn()
    conn.execute("DELETE FROM menu_items WHERE item_id=?", (item_id,))
    conn.commit()
    conn.close()

def get_menu_df(only_available=False):
    conn = get_conn()
    q = "SELECT * FROM menu_items"
    if only_available:
        q += " WHERE available=1"
    q += " ORDER BY category, name"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df

def create_invoice_from_cart(cart_df, table_no, waiter_name, payment_method):
    """
    cart_df columns required:
    item_id, name, category, qty, price, cost, tax_percent
    """
    if cart_df.empty:
        raise ValueError("Cart is empty")

    df = cart_df.copy()
    df["line_subtotal"] = df["qty"] * df["price"]
    df["line_tax"] = (df["line_subtotal"] * df["tax_percent"]) / 100
    df["line_total"] = df["line_subtotal"] + df["line_tax"]

    subtotal = float(df["line_subtotal"].sum())
    tax_amount = float(df["line_tax"].sum())
    total = float(df["line_total"].sum())

    invoice_no = f"INV-{uuid.uuid4().hex[:8].upper()}"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO invoices (invoice_no, table_no, waiter_name, payment_method, subtotal, tax_amount, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (invoice_no, table_no, waiter_name, payment_method, subtotal, tax_amount, total))

    invoice_id = cur.lastrowid

    for _, r in df.iterrows():
        cur.execute("""
            INSERT INTO invoice_items
            (invoice_id, item_id, item_name, category, qty, unit_price, unit_cost, tax_percent,
             line_subtotal, line_tax, line_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            int(r["item_id"]),
            str(r["name"]),
            str(r["category"]),
            int(r["qty"]),
            float(r["price"]),
            float(r["cost"]),
            float(r["tax_percent"]),
            float(r["line_subtotal"]),
            float(r["line_tax"]),
            float(r["line_total"])
        ))

    conn.commit()
    conn.close()

    return invoice_no, invoice_id, subtotal, tax_amount, total