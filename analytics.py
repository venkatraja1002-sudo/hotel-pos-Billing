import pandas as pd
from db import get_conn

def load_sales_tables():
    conn = get_conn()
    inv = pd.read_sql_query("SELECT * FROM invoices ORDER BY date_time DESC", conn)
    items = pd.read_sql_query("SELECT * FROM invoice_items ORDER BY line_id DESC", conn)
    conn.close()
    return inv, items

def kpis(inv_df, items_df):
    if inv_df.empty:
        return {"revenue": 0, "profit": 0, "invoices": 0, "avg_bill": 0}

    revenue = float(inv_df["total"].sum())
    invoices = int(inv_df.shape[0])
    avg_bill = float(inv_df["total"].mean())

    if items_df.empty:
        profit = 0.0
    else:
        profit = float(((items_df["unit_price"] - items_df["unit_cost"]) * items_df["qty"]).sum())

    return {"revenue": revenue, "profit": profit, "invoices": invoices, "avg_bill": avg_bill}

def daily_revenue(inv_df):
    if inv_df.empty:
        return inv_df
    df = inv_df.copy()
    df["date"] = pd.to_datetime(df["date_time"]).dt.date
    return df.groupby("date").agg(revenue=("total", "sum")).reset_index().sort_values("date")

def top_items(items_df, n=10):
    if items_df.empty:
        return items_df
    return (items_df.groupby("item_name")
            .agg(qty_sold=("qty", "sum"), revenue=("line_total", "sum"))
            .sort_values("revenue", ascending=False)
            .head(n)
            .reset_index())

def category_sales(items_df):
    if items_df.empty:
        return items_df
    return (items_df.groupby("category")
            .agg(qty_sold=("qty", "sum"), revenue=("line_total", "sum"))
            .sort_values("revenue", ascending=False)
            .reset_index())