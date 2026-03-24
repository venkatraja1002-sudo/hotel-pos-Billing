# hotel-pos-Billing
Streamlit-based Hotel/Restaurant POS Billing system with Admin menu management (image upload), sales analytics dashboard, and PDF invoice generation using SQLite.

# Hotel POS + Analytics (Streamlit)

A Hotel/Restaurant POS billing system built using **Streamlit + SQLite**.
Includes:
- POS Billing page (menu cards + image + search + qty)
- Admin page (add/edit/delete menu items + upload image)
- Analytics dashboard (revenue, profit, invoices, trends)
- PDF Invoice download (ReportLab)

## Features
✅ Menu management (Admin)
- Add menu items with image upload
- Edit/replace images
- Mark items available/unavailable
- Delete items

✅ POS Billing
- Search menu items by name
- Filter by category
- Add/Remove items and auto-update quantity
- Select Table number (1–10), Waiter name, Payment method
- Save invoices to SQLite
- Generate and download PDF invoice

✅ Analytics
- Revenue, Profit, #Invoices, Avg Bill
- Daily revenue trend
- Top selling items
- Category sales summary
- Export invoices + invoice_items as CSV

## Tech Stack
- Python
- Streamlit
- SQLite
- Pandas
- ReportLab (PDF)

## Setup
```bash
git clone <your-repo-url>
cd hotel-pos-analytics-streamlit
pip install -r requirements.txt
streamlit run app.py

How to Use

Open Admin Menu

Add menu items (with images)

Open POS Billing

Select items and generate bill

Save invoice + download PDF

Open Analytics

See sales insights and export CSV
