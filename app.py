import streamlit as st
import pandas as pd

from db import init_db
from services import (
    add_menu_item, update_menu_item, delete_menu_item,
    get_menu_df, create_invoice_from_cart
)
from analytics import load_sales_tables, kpis, daily_revenue, top_items, category_sales
from pdf_utils import make_invoice_pdf


# -------------------- App Setup --------------------
st.set_page_config(page_title="Hotel POS + Admin + Analytics", layout="wide")
init_db()

# -------------------- Session State --------------------
if "cart" not in st.session_state:
    st.session_state.cart = {}  # {item_id: qty}

if "last_pdf" not in st.session_state:
    st.session_state.last_pdf = None

if "last_pdf_name" not in st.session_state:
    st.session_state.last_pdf_name = None


def add_qty(item_id: int, delta: int):
    cur = st.session_state.cart.get(item_id, 0)
    new_qty = cur + delta
    if new_qty <= 0:
        st.session_state.cart.pop(item_id, None)
    else:
        st.session_state.cart[item_id] = new_qty


def clear_cart():
    st.session_state.cart = {}
    st.session_state.last_pdf = None
    st.session_state.last_pdf_name = None


# -------------------- Sidebar --------------------
st.sidebar.title("🍽️ Hotel POS")
page = st.sidebar.radio("Go to", ["POS Billing", "Admin Menu", "Analytics"])

st.sidebar.divider()
restaurant_name = st.sidebar.text_input("Restaurant name", value="Hotel Raja")
table_no = st.sidebar.selectbox("Table number", [f"Table {i}" for i in range(1, 11)], index=0)
waiter_name = st.sidebar.selectbox("Waiter name", ["Aswin", "Venkat", "Kumar", "Suriya", "Suresh"], index=0)
payment_method = st.sidebar.selectbox("Payment method", ["CASH", "UPI", "CARD", "NETBANKING"], index=0)


# -------------------- POS BILLING --------------------
if page == "POS Billing":
    st.title("🧾 Hotel Raja (Images + Search + Qty)")

    menu = get_menu_df(only_available=True)
    if menu.empty:
        st.warning("No menu items found. Add items in Admin Menu.")
        st.stop()

    # Top filters (NO columns nesting here; keep simple)
    search = st.text_input("Search menu item name", value="", placeholder="Type: biryani, dosa, tea...")
    cats = sorted(menu["category"].unique().tolist())
    selected_cat = st.selectbox("Category", ["All"] + cats)

    filtered = menu.copy()
    if selected_cat != "All":
        filtered = filtered[filtered["category"] == selected_cat]
    if search.strip():
        s = search.strip().lower()
        filtered = filtered[filtered["name"].str.lower().str.contains(s)]

    # Main Layout
    left, right = st.columns([2.3, 1.2], gap="large")

    # -------- LEFT: MENU GRID --------
    with left:
        st.subheader("📌 Menu")

        if filtered.empty:
            st.info("No items match. Try a different search.")
        else:
            cols_per_row = 3
            items = filtered.to_dict("records")

            # Grid: cards row + controls row (NO nested columns inside cards)
            for i in range(0, len(items), cols_per_row):
                row = items[i:i + cols_per_row]

                # 1) CARD ROW
                card_cols = st.columns(cols_per_row)
                for idx, it in enumerate(row):
                    item_id = int(it["item_id"])
                    qty_now = st.session_state.cart.get(item_id, 0)

                    with card_cols[idx]:
                        if it["image_blob"]:
                            st.image(it["image_blob"], use_container_width=True)
                        else:
                            st.write("🖼️ No image")

                        st.markdown(f"**{it['name']}**")
                        st.write(f"₹{float(it['price']):.2f} | {it['category']}")
                        st.write(f"Qty: {qty_now}")

                # 2) CONTROLS ROW (IMPORTANT: do not create nested columns here)
                ctrl_cols = st.columns(cols_per_row)
                for idx, it in enumerate(row):
                    item_id = int(it["item_id"])
                    qty_now = st.session_state.cart.get(item_id, 0)

                    # Use column objects directly to avoid nesting
                    ctrl_cols[idx].button("➖ Remove", key=f"m_{item_id}", on_click=add_qty, args=(item_id, -1))
                    ctrl_cols[idx].markdown(
                        f"<div style='text-align:center; font-size:18px;'><b>{qty_now}</b></div>",
                        unsafe_allow_html=True
                    )
                    ctrl_cols[idx].button("➕ Add", key=f"p_{item_id}", on_click=add_qty, args=(item_id, +1))

                st.divider()

    # -------- RIGHT: BILL / CART --------
    with right:
        st.subheader("🧾 Current Bill")

        if not st.session_state.cart:
            st.info("No items selected. Use Add/Remove buttons from the menu.")
            st.caption(f"{table_no} | Waiter: {waiter_name} | Payment: {payment_method}")
            st.stop()

        # Build cart dataframe from session cart
        cart_rows = []
        for item_id, qty in st.session_state.cart.items():
            it = menu[menu["item_id"] == item_id].iloc[0]
            cart_rows.append({
                "item_id": int(item_id),
                "name": str(it["name"]),
                "category": str(it["category"]),
                "qty": int(qty),
                "price": float(it["price"]),
                "cost": float(it["cost"]),
                "tax_percent": float(it["tax_percent"]),
            })

        cart_df = pd.DataFrame(cart_rows)

        # Compute totals preview
        preview = cart_df.copy()
        preview["line_subtotal"] = preview["qty"] * preview["price"]
        preview["line_tax"] = (preview["line_subtotal"] * preview["tax_percent"]) / 100
        preview["line_total"] = preview["line_subtotal"] + preview["line_tax"]

        subtotal = float(preview["line_subtotal"].sum())
        tax_amount = float(preview["line_tax"].sum())
        total = float(preview["line_total"].sum())

        show = preview[["name", "qty", "price", "tax_percent", "line_total"]].copy()
        show.columns = ["Item", "Qty", "Price", "Tax%", "Amount"]
        st.dataframe(show, use_container_width=True, hide_index=True)

        st.markdown(f"### ✅ Total: ₹{total:.2f}")
        st.caption(f"{table_no} | Waiter: {waiter_name} | Payment: {payment_method}")

        st.write("### Cart Controls")
        # IMPORTANT: avoid st.columns here too (for max compatibility)
        for _, r in cart_df.sort_values("name").iterrows():
            item_id = int(r["item_id"])
            st.write(f"**{r['name']}** — qty: {int(r['qty'])}")
            st.button("➕ Add one", key=f"cart_add_{item_id}", on_click=add_qty, args=(item_id, +1))
            st.button("➖ Remove one", key=f"cart_rem_{item_id}", on_click=add_qty, args=(item_id, -1))
            st.divider()

        st.button("🧹 Clear Bill", on_click=clear_cart)

        if st.button("🧾 Save Sale + Generate PDF"):
            invoice_no, invoice_id, s_sub, s_tax, s_total = create_invoice_from_cart(
                cart_df,
                table_no=table_no,
                waiter_name=waiter_name,
                payment_method=payment_method
            )

            pdf_table = show.copy()
            pdf_bytes = make_invoice_pdf(
                restaurant_name=restaurant_name,
                invoice_no=invoice_no,
                table_no=table_no,
                waiter_name=waiter_name,
                payment_method=payment_method,
                cart_df=pdf_table,
                subtotal=s_sub,
                tax_amount=s_tax,
                total=s_total
            )

            st.session_state.last_pdf = pdf_bytes
            st.session_state.last_pdf_name = f"{invoice_no}.pdf"
            st.success(f"Saved invoice {invoice_no} (ID: {invoice_id})")

        if st.session_state.last_pdf:
            st.download_button(
                "⬇️ Download Invoice PDF",
                data=st.session_state.last_pdf,
                file_name=st.session_state.last_pdf_name or "invoice.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# -------------------- ADMIN MENU --------------------
elif page == "Admin Menu":
    st.title("🛠️ Admin Menu (Add Items + Upload Photo)")

    st.subheader("➕ Add new menu item")
    with st.form("add_menu"):
        name = st.text_input("Item name")
        category = st.text_input("Category", value="Main")
        price = st.number_input("Price (₹)", min_value=0.0, value=100.0)
        cost = st.number_input("Cost (₹)", min_value=0.0, value=60.0)
        tax_percent = st.number_input("Tax %", min_value=0.0, value=5.0)
        available = st.selectbox("Available", [1, 0], format_func=lambda x: "Yes" if x == 1 else "No")
        photo = st.file_uploader("Upload item photo (jpg/png)", type=["jpg", "jpeg", "png"])

        if photo is not None:
            st.image(photo, width=180)

        ok = st.form_submit_button("Add item")
        if ok:
            if not name.strip():
                st.error("Item name is required.")
            else:
                img_bytes, img_mime = None, None
                if photo is not None:
                    img_bytes = photo.getvalue()
                    img_mime = photo.type

                add_menu_item(
                    name=name.strip(),
                    category=category.strip() or "General",
                    price=float(price),
                    cost=float(cost),
                    tax_percent=float(tax_percent),
                    available=int(available),
                    image_bytes=img_bytes,
                    image_mime=img_mime
                )
                st.success("Menu item added!")

    st.divider()
    st.subheader("📋 Edit / Delete menu items")

    menu = get_menu_df(only_available=False)
    if menu.empty:
        st.info("No items yet. Add above.")
        st.stop()

    options = menu[["item_id", "name", "category"]].copy()
    options["label"] = options.apply(lambda r: f"{r['name']} ({r['category']}) - ID {r['item_id']}", axis=1)

    selected_label = st.selectbox("Select item", options["label"].tolist())
    item_id = int(options[options["label"] == selected_label]["item_id"].iloc[0])
    item = menu[menu["item_id"] == item_id].iloc[0]

    if item["image_blob"]:
        st.image(item["image_blob"], width=260)
    else:
        st.write("🖼️ No image for this item.")

    with st.form("edit_form"):
        name2 = st.text_input("Item name", value=str(item["name"]))
        cat2 = st.text_input("Category", value=str(item["category"]))
        price2 = st.number_input("Price (₹)", min_value=0.0, value=float(item["price"]))
        cost2 = st.number_input("Cost (₹)", min_value=0.0, value=float(item["cost"]))
        tax2 = st.number_input("Tax %", min_value=0.0, value=float(item["tax_percent"]))
        avail2 = st.selectbox(
            "Available",
            [1, 0],
            index=0 if int(item["available"]) == 1 else 1,
            format_func=lambda x: "Yes" if x == 1 else "No"
        )

        new_photo = st.file_uploader("Replace photo (optional)", type=["jpg", "jpeg", "png"], key="replace_photo")
        keep_old = st.checkbox("Keep existing photo if no new upload", value=True)

        save = st.form_submit_button("Save changes")
        if save:
            img_bytes, img_mime = None, None
            if new_photo is not None:
                img_bytes = new_photo.getvalue()
                img_mime = new_photo.type

            update_menu_item(
                item_id=item_id,
                name=name2.strip(),
                category=cat2.strip() or "General",
                price=float(price2),
                cost=float(cost2),
                tax_percent=float(tax2),
                available=int(avail2),
                image_bytes=img_bytes,
                image_mime=img_mime,
                keep_old_image=bool(keep_old)
            )
            st.success("Updated!")

    if st.button("🗑️ Delete this item"):
        delete_menu_item(item_id)
        st.warning("Deleted. Refreshing...")
        st.rerun()


# -------------------- ANALYTICS --------------------
else:
    st.title("📊 Analytics Dashboard")

    inv, items = load_sales_tables()
    metrics = kpis(inv, items)

    # Use columns here at root level (safe)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue", f"₹{metrics['revenue']:.2f}")
    m2.metric("Profit", f"₹{metrics['profit']:.2f}")
    m3.metric("Invoices", f"{metrics['invoices']}")
    m4.metric("Avg Bill", f"₹{metrics['avg_bill']:.2f}")

    st.divider()

    st.subheader("Daily Revenue Trend")
    trend = daily_revenue(inv)
    if trend.empty:
        st.info("No sales yet.")
    else:
        st.line_chart(trend.set_index("date"))

    st.subheader("Top Selling Items")
    top = top_items(items, n=10)
    if not top.empty:
        st.dataframe(top, use_container_width=True, hide_index=True)
    else:
        st.info("No items sold yet.")

    st.subheader("Category Sales")
    cat = category_sales(items)
    if not cat.empty:
        st.dataframe(cat, use_container_width=True, hide_index=True)
    else:
        st.info("No category sales yet.")

    st.subheader("Export CSV")
    st.download_button(
        "⬇️ Download invoices CSV",
        data=inv.to_csv(index=False).encode("utf-8"),
        file_name="invoices.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.download_button(
        "⬇️ Download invoice_items CSV",
        data=items.to_csv(index=False).encode("utf-8"),
        file_name="invoice_items.csv",
        mime="text/csv",
        use_container_width=True
    )