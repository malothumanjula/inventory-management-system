import mysql.connector
from tkinter import *
from tkinter import ttk, messagebox
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import math
import pathlib
import sys

# ------------------ Database Connection ------------------
def connect_db():
    try:
        con = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root123",  # change to your MySQL password
            database="inventorydb"
        )
        return con
    except Exception as e:
        messagebox.showerror("Database Error", f"Unable to connect to MySQL:\n{e}")
        return None

# ------------------ PRODUCT CRUD ------------------
def add_product():
    con = connect_db()
    if not con: return
    cur = con.cursor()
    try:
        # map names to ids
        cur.execute("SELECT cid FROM categories WHERE category_name=%s", (category_name_var.get(),))
        r = cur.fetchone()
        if not r:
            messagebox.showerror("Error", "Please select a valid Category.")
            return
        cid = r[0]

        cur.execute("SELECT bid FROM brands WHERE bname=%s", (brand_name_var.get(),))
        r = cur.fetchone()
        if not r:
            messagebox.showerror("Error", "Please select a valid Brand.")
            return
        bid = r[0]

        cur.execute("SELECT sid FROM stores WHERE sname=%s", (store_name_var.get(),))
        r = cur.fetchone()
        if not r:
            messagebox.showerror("Error", "Please select a valid Store.")
            return
        sid = r[0]

        # insert product (pid is auto-increment)
        cur.execute("""
            INSERT INTO product (cid, bid, sid, pname, p_stock, price, added_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (cid, bid, sid, pname_var.get().strip(), int_or_zero(stock_var.get()), float_or_zero(price_var.get()), date.today()))
        con.commit()
        messagebox.showinfo("Success", "✅ Product added successfully!")
        fetch_products()
        clear_product_fields()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add product:\n{e}")
    finally:
        con.close()

def update_product():
    if not pid_var.get():
        messagebox.showerror("Error", "Select a product to update.")
        return
    con = connect_db()
    if not con: return
    cur = con.cursor()
    try:
        cur.execute("UPDATE product SET pname=%s, p_stock=%s, price=%s WHERE pid=%s",
                    (pname_var.get().strip(), int_or_zero(stock_var.get()), float_or_zero(price_var.get()), pid_var.get()))
        con.commit()
        messagebox.showinfo("Updated", "✏️ Product updated successfully!")
        fetch_products()
        clear_product_fields()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update product:\n{e}")
    finally:
        con.close()

def delete_product():
    if not pid_var.get():
        messagebox.showerror("Error", "Select a product to delete.")
        return
    con = connect_db()
    if not con: return
    cur = con.cursor()
    try:
        # confirm
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            return
        cur.execute("DELETE FROM product WHERE pid=%s", (pid_var.get(),))
        con.commit()
        messagebox.showinfo("Deleted", "🗑️ Product deleted successfully!")
        fetch_products()
        clear_product_fields()
    except mysql.connector.IntegrityError as ie:
        messagebox.showerror("FK Error", f"Cannot delete product — it's referenced elsewhere.\n{ie}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete product:\n{e}")
    finally:
        con.close()

def clear_product_fields():
    pid_var.set("")
    pname_var.set("")
    stock_var.set("")
    price_var.set("")
    category_name_var.set("")
    brand_name_var.set("")
    store_name_var.set("")

# ------------------ HELP PARSERS ------------------
def int_or_zero(s):
    try:
        return int(s)
    except:
        return 0

def float_or_zero(s):
    try:
        return float(s)
    except:
        return 0.0

# ------------------ FETCH & POPULATE ------------------
def fetch_products():
    con = connect_db()
    if not con: return
    cur = con.cursor()
    cur.execute("""
        SELECT p.pid, COALESCE(c.category_name,''), COALESCE(b.bname,''), COALESCE(s.sname,''), p.pname, p.p_stock, p.price, p.added_date
        FROM product p
        LEFT JOIN categories c ON p.cid=c.cid
        LEFT JOIN brands b ON p.bid=b.bid
        LEFT JOIN stores s ON p.sid=s.sid
        ORDER BY p.pid DESC
    """)
    rows = cur.fetchall()
    product_table.delete(*product_table.get_children())
    for row in rows:
        product_table.insert('', END, values=row)
    con.close()

def get_product_from_tree(event):
    cur_item = product_table.focus()
    if not cur_item:
        return
    values = product_table.item(cur_item).get('values')
    if not values:
        return
    # values order: pid, category, brand, store, pname, stock, price, date
    pid_var.set(values[0])
    category_name_var.set(values[1])
    brand_name_var.set(values[2])
    store_name_var.set(values[3])
    pname_var.set(values[4])
    stock_var.set(values[5])
    price_var.set(values[6])

# ------------------ DROPDOWNS ------------------
def load_dropdown_data():
    con = connect_db()
    if not con: return
    cur = con.cursor()
    cur.execute("SELECT category_name FROM categories ORDER BY category_name")
    category_combo['values'] = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT bname FROM brands ORDER BY bname")
    brand_combo['values'] = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT sname FROM stores ORDER BY sname")
    store_combo['values'] = [r[0] for r in cur.fetchall()]

    con.close()

# ------------------ CUSTOMER MODULE ------------------
def add_customer():
    con = connect_db()
    if not con: return
    cur = con.cursor()
    try:
        name = cust_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Enter customer name.")
            return
        cur.execute("INSERT INTO customers (cust_name, phone, email) VALUES (%s,%s,%s)",
                    (name, cust_phone_var.get().strip(), cust_email_var.get().strip()))
        con.commit()
        messagebox.showinfo("Success", "✅ Customer added.")
        fetch_customers()
        cust_name_var.set("")
        cust_phone_var.set("")
        cust_email_var.set("")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add customer:\n{e}")
    finally:
        con.close()

def fetch_customers():
    con = connect_db()
    if not con: return
    cur = con.cursor()
    cur.execute("SELECT cust_id, cust_name, phone, email FROM customers ORDER BY cust_id DESC")
    rows = cur.fetchall()
    customer_table.delete(*customer_table.get_children())
    for r in rows:
        customer_table.insert('', END, values=r)
    con.close()

# ------------------ TRANSACTION + INVOICE ------------------
def make_transaction():
    con = connect_db()
    if not con: return
    cur = con.cursor()
    try:
        # validate inputs
        cust_id = int_or_zero(trans_cust_id_var.get())
        pid = int_or_zero(trans_pid_var.get())
        qty = int_or_zero(trans_qty_var.get())
        if cust_id <= 0 or pid <= 0 or qty <= 0:
            messagebox.showerror("Error", "Enter valid Customer ID, Product ID and Quantity.")
            return

        # fetch product
        cur.execute("SELECT pname, price, p_stock FROM product WHERE pid=%s", (pid,))
        prod = cur.fetchone()
        if not prod:
            messagebox.showerror("Error", "Invalid Product ID.")
            return
        pname, price, stock = prod
        if qty > stock:
            messagebox.showerror("Error", f"Only {stock} units available.")
            return

        total = float(price) * qty

        # insert transaction
        cur.execute("INSERT INTO transactions (cust_id, pid, quantity, total_price, trans_date) VALUES (%s,%s,%s,%s,%s)",
                    (cust_id, pid, qty, total, date.today()))
        trans_id = cur.lastrowid

        # update stock
        cur.execute("UPDATE product SET p_stock = p_stock - %s WHERE pid=%s", (qty, pid))

        # invoice record
        cur.execute("INSERT INTO invoice (trans_id, invoice_date, amount) VALUES (%s,%s,%s)", (trans_id, date.today(), total))

        con.commit()
        messagebox.showinfo("Success", f"Transaction done. Total: ₹{total:.2f}")

        # refresh displays
        fetch_products()
        fetch_transactions()

        # generate PDF invoice
        generate_invoice_pdf(trans_id, cust_id, pname, qty, price, total)

        # clear transaction inputs
        trans_cust_id_var.set("")
        trans_pid_var.set("")
        trans_qty_var.set("")

    except Exception as e:
        messagebox.showerror("Error", f"Transaction failed:\n{e}")
    finally:
        con.close()

def fetch_transactions():
    con = connect_db()
    if not con: return
    cur = con.cursor()
    cur.execute("SELECT trans_id, cust_id, pid, quantity, total_price, trans_date FROM transactions ORDER BY trans_id DESC")
    rows = cur.fetchall()
    transaction_table.delete(*transaction_table.get_children())
    for r in rows:
        transaction_table.insert('', END, values=r)
    con.close()

def generate_invoice_pdf(trans_id, cust_id, pname, qty, price, total):
    folder = "invoices"
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"invoice_{trans_id}.pdf")

    pdf = canvas.Canvas(filename, pagesize=A4)
    pdf.setTitle(f"Invoice #{trans_id}")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(200, 800, "INVOICE")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Invoice ID: {trans_id}")
    pdf.drawString(50, 740, f"Customer ID: {cust_id}")
    pdf.drawString(50, 720, f"Date: {date.today().strftime('%d-%m-%Y')}")
    pdf.line(50, 710, 550, 710)
    pdf.drawString(50, 690, "Product Name")
    pdf.drawString(250, 690, "Qty")
    pdf.drawString(300, 690, "Price (₹)")
    pdf.drawString(400, 690, "Total (₹)")
    pdf.line(50, 685, 550, 685)
    pdf.drawString(50, 660, str(pname))
    pdf.drawString(250, 660, str(qty))
    pdf.drawString(300, 660, f"{float(price):.2f}")
    pdf.drawString(400, 660, f"{float(total):.2f}")
    pdf.line(50, 640, 550, 640)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(350, 620, f"Grand Total: ₹{float(total):.2f}")
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(50, 580, "Thank you for your purchase!")
    pdf.save()

    # Offer to open file
    if messagebox.askyesno("Invoice Created", f"Invoice saved as:\n{filename}\n\nOpen it now?"):
        try:
            if sys.platform.startswith('win'):
                os.startfile(os.path.abspath(filename))
            elif sys.platform == 'darwin':
                os.system(f'open "{filename}"')
            else:
                os.system(f'xdg-open "{filename}"')
        except Exception:
            messagebox.showinfo("Saved", f"Invoice saved at:\n{filename}")

# ------------------ GUI BUILD ------------------
root = Tk()
root.title("Inventory Management System")
root.geometry("980x720")
root.config(bg="#E8F0FE")

title = Label(root, text="Inventory Management System", font=("Arial", 20, "bold"),
              bg="#4285F4", fg="white", pady=10)
title.pack(fill=X)

notebook = ttk.Notebook(root)
notebook.place(x=10, y=70, width=960, height=620)

# ---------- Products Tab ----------
product_tab = Frame(notebook, bg="white")
notebook.add(product_tab, text="Products")

pid_var = StringVar()
pname_var = StringVar()
stock_var = StringVar()
price_var = StringVar()
category_name_var = StringVar()
brand_name_var = StringVar()
store_name_var = StringVar()

frm = Frame(product_tab, bd=2, relief=RIDGE, bg="white")
frm.place(x=10, y=10, width=940, height=220)

Label(frm, text="Product ID", bg="white").grid(row=0, column=0, padx=8, pady=6, sticky="w")
Entry(frm, textvariable=pid_var, state='readonly').grid(row=0, column=1, padx=8, pady=6)

Label(frm, text="Name", bg="white").grid(row=0, column=2, padx=8, pady=6, sticky="w")
Entry(frm, textvariable=pname_var).grid(row=0, column=3, padx=8, pady=6)

Label(frm, text="Category", bg="white").grid(row=1, column=0, padx=8, pady=6, sticky="w")
category_combo = ttk.Combobox(frm, textvariable=category_name_var, state="readonly")
category_combo.grid(row=1, column=1, padx=8, pady=6)

Label(frm, text="Brand", bg="white").grid(row=1, column=2, padx=8, pady=6, sticky="w")
brand_combo = ttk.Combobox(frm, textvariable=brand_name_var, state="readonly")
brand_combo.grid(row=1, column=3, padx=8, pady=6)

Label(frm, text="Store", bg="white").grid(row=2, column=0, padx=8, pady=6, sticky="w")
store_combo = ttk.Combobox(frm, textvariable=store_name_var, state="readonly")
store_combo.grid(row=2, column=1, padx=8, pady=6)

Label(frm, text="Stock", bg="white").grid(row=2, column=2, padx=8, pady=6, sticky="w")
Entry(frm, textvariable=stock_var).grid(row=2, column=3, padx=8, pady=6)

Label(frm, text="Price", bg="white").grid(row=3, column=0, padx=8, pady=6, sticky="w")
Entry(frm, textvariable=price_var).grid(row=3, column=1, padx=8, pady=6)

Button(frm, text="Add", command=add_product, bg="#34A853", fg="white", width=10).grid(row=4, column=0, padx=8, pady=10)
Button(frm, text="Update", command=update_product, bg="#FBBC05", fg="white", width=10).grid(row=4, column=1, padx=8, pady=10)
Button(frm, text="Delete", command=delete_product, bg="#EA4335", fg="white", width=10).grid(row=4, column=2, padx=8, pady=10)
Button(frm, text="Clear", command=clear_product_fields, bg="#4285F4", fg="white", width=10).grid(row=4, column=3, padx=8, pady=10)

table_frame = Frame(product_tab, bd=2, relief=RIDGE, bg="white")
table_frame.place(x=10, y=240, width=940, height=360)

scroll_x = Scrollbar(table_frame, orient=HORIZONTAL)
scroll_y = Scrollbar(table_frame, orient=VERTICAL)
product_table = ttk.Treeview(table_frame,
    columns=("pid", "category", "brand", "store", "pname", "stock", "price", "date"),
    xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
scroll_x.pack(side=BOTTOM, fill=X)
scroll_y.pack(side=RIGHT, fill=Y)
scroll_x.config(command=product_table.xview)
scroll_y.config(command=product_table.yview)

for col in ("pid", "category", "brand", "store", "pname", "stock", "price", "date"):
    product_table.heading(col, text=col.upper())
    product_table.column(col, width=110)
product_table["show"] = "headings"
product_table.pack(fill=BOTH, expand=1)
product_table.bind("<ButtonRelease-1>", get_product_from_tree)

# ---------- Customers Tab ----------
customer_tab = Frame(notebook, bg="white")
notebook.add(customer_tab, text="Customers")

cust_name_var = StringVar()
cust_phone_var = StringVar()
cust_email_var = StringVar()

Label(customer_tab, text="Name", bg="white").grid(row=0, column=0, padx=8, pady=6, sticky="w")
Entry(customer_tab, textvariable=cust_name_var).grid(row=0, column=1, padx=8, pady=6)
Label(customer_tab, text="Phone", bg="white").grid(row=1, column=0, padx=8, pady=6, sticky="w")
Entry(customer_tab, textvariable=cust_phone_var).grid(row=1, column=1, padx=8, pady=6)
Label(customer_tab, text="Email", bg="white").grid(row=2, column=0, padx=8, pady=6, sticky="w")
Entry(customer_tab, textvariable=cust_email_var).grid(row=2, column=1, padx=8, pady=6)
Button(customer_tab, text="Add Customer", command=add_customer, bg="#34A853", fg="white", width=15).grid(row=3, column=0, padx=8, pady=10)

customer_table = ttk.Treeview(customer_tab, columns=("cust_id", "cust_name", "phone", "email"), show="headings")
for col in customer_table["columns"]:
    customer_table.heading(col, text=col.replace("_"," ").title())
customer_table.place(x=350, y=10, width=580, height=300)
fetch_customers()

# ---------- Transactions Tab ----------
transaction_tab = Frame(notebook, bg="white")
notebook.add(transaction_tab, text="Transactions")

trans_cust_id_var = StringVar()
trans_pid_var = StringVar()
trans_qty_var = StringVar()

Label(transaction_tab, text="Customer ID", bg="white").grid(row=0, column=0, padx=8, pady=6, sticky="w")
Entry(transaction_tab, textvariable=trans_cust_id_var).grid(row=0, column=1, padx=8, pady=6)
Label(transaction_tab, text="Product ID", bg="white").grid(row=1, column=0, padx=8, pady=6, sticky="w")
Entry(transaction_tab, textvariable=trans_pid_var).grid(row=1, column=1, padx=8, pady=6)
Label(transaction_tab, text="Quantity", bg="white").grid(row=2, column=0, padx=8, pady=6, sticky="w")
Entry(transaction_tab, textvariable=trans_qty_var).grid(row=2, column=1, padx=8, pady=6)

Button(transaction_tab, text="Make Transaction", command=make_transaction, bg="#4285F4", fg="white", width=16).grid(row=3, column=0, padx=8, pady=10)

transaction_table = ttk.Treeview(transaction_tab, columns=("trans_id", "cust_id", "pid", "quantity", "total_price", "trans_date"), show="headings")
for col in transaction_table["columns"]:
    transaction_table.heading(col, text=col.replace("_"," ").title())
transaction_table.place(x=350, y=10, width=580, height=300)
fetch_transactions()

# Load dropdowns and products initially
load_dropdown_data()
fetch_products()

root.mainloop()
