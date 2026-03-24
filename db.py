import sqlite3
from pathlib import Path

DB_PATH = Path("hotel_pos.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Menu items (store image in DB as BLOB)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu_items(
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        cost REAL DEFAULT 0,
        tax_percent REAL DEFAULT 0,
        available INTEGER DEFAULT 1,
        image_blob BLOB,
        image_mime TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Invoices (hotel bills)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices(
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE,
        date_time TEXT DEFAULT CURRENT_TIMESTAMP,
        table_no TEXT,
        waiter_name TEXT,
        payment_method TEXT,
        subtotal REAL,
        tax_amount REAL,
        total REAL
    );
    """)

    # Bill line items
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items(
        line_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        item_id INTEGER,
        item_name TEXT,
        category TEXT,
        qty INTEGER,
        unit_price REAL,
        unit_cost REAL,
        tax_percent REAL,
        line_subtotal REAL,
        line_tax REAL,
        line_total REAL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(invoice_id),
        FOREIGN KEY(item_id) REFERENCES menu_items(item_id)
    );
    """)

    conn.commit()
    conn.close()