import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# Database setup
conn = sqlite3.connect("wallet_system.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT UNIQUE,
    created_at TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS Wallets (
    wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    balance REAL DEFAULT 0,
    updated_at TEXT,
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS Transactions (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_wallet INTEGER,
    receiver_wallet INTEGER,
    amount REAL,
    txn_type TEXT,
    timestamp TEXT,
    note TEXT,
    FOREIGN KEY(sender_wallet) REFERENCES Wallets(wallet_id),
    FOREIGN KEY(receiver_wallet) REFERENCES Wallets(wallet_id)
)''')

conn.commit()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- WALLET FUNCTIONS ----------
def get_wallet_id(phone):
    c.execute("SELECT Wallets.wallet_id FROM Users JOIN Wallets ON Users.user_id = Wallets.user_id WHERE phone = ?", (phone,))
    result = c.fetchone()
    return result[0] if result else None

def register_user():
    name = simpledialog.askstring("Register User", "👤 Enter name:")
    phone = simpledialog.askstring("Register User", "📱 Enter phone number:")
    if name and phone:
        try:
            c.execute("INSERT INTO Users (name, phone, created_at) VALUES (?, ?, ?)", (name, phone, now()))
            user_id = c.lastrowid
            c.execute("INSERT INTO Wallets (user_id, balance, updated_at) VALUES (?, ?, ?)", (user_id, 0, now()))
            conn.commit()
            messagebox.showinfo("✅ Success", f"{name} registered successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror("⚠️ Error", "Phone number already registered.")

def add_money():
    phone = simpledialog.askstring("Add Money", "📱 Enter phone number:")
    amount = simpledialog.askfloat("Add Money", "💸 Enter amount:")
    if phone and amount:
        wallet_id = get_wallet_id(phone)
        if wallet_id:
            c.execute("UPDATE Wallets SET balance = balance + ?, updated_at = ? WHERE wallet_id = ?", (amount, now(), wallet_id))
            c.execute("INSERT INTO Transactions (receiver_wallet, amount, txn_type, timestamp, note) VALUES (?, ?, 'Add Money', ?, 'Top-up')", (wallet_id, amount, now()))
            conn.commit()
            messagebox.showinfo("✅ Success", f"₹{amount} added successfully!")
        else:
            messagebox.showerror("⚠️ Error", "Wallet not found.")

def transfer_money():
    sender = simpledialog.askstring("Transfer", "📤 Sender phone number:")
    receiver = simpledialog.askstring("Transfer", "📥 Receiver phone number:")
    amount = simpledialog.askfloat("Transfer", "💸 Enter amount:")
    if sender and receiver and amount:
        sender_id = get_wallet_id(sender)
        receiver_id = get_wallet_id(receiver)
        if not sender_id or not receiver_id:
            messagebox.showerror("⚠️ Error", "Invalid sender or receiver.")
            return
        c.execute("SELECT balance FROM Wallets WHERE wallet_id = ?", (sender_id,))
        balance = c.fetchone()[0]
        if balance < amount:
            messagebox.showerror("🚫 Error", "Insufficient balance.")
            return
        c.execute("UPDATE Wallets SET balance = balance - ?, updated_at = ? WHERE wallet_id = ?", (amount, now(), sender_id))
        c.execute("UPDATE Wallets SET balance = balance + ?, updated_at = ? WHERE wallet_id = ?", (amount, now(), receiver_id))
        c.execute("INSERT INTO Transactions (sender_wallet, receiver_wallet, amount, txn_type, timestamp, note) VALUES (?, ?, ?, 'Transfer', ?, 'P2P Transfer')", (sender_id, receiver_id, amount, now()))
        conn.commit()
        messagebox.showinfo("✅ Success", f"₹{amount} transferred successfully.")

def view_balance():
    phone = simpledialog.askstring("View Balance", "📱 Enter phone number:")
    if phone:
        wallet_id = get_wallet_id(phone)
        if wallet_id:
            c.execute("SELECT balance FROM Wallets WHERE wallet_id = ?", (wallet_id,))
            balance = c.fetchone()[0]
            messagebox.showinfo("💰 Wallet Balance", f"Balance for {phone}: ₹{balance}")
        else:
            messagebox.showerror("⚠️ Error", "Wallet not found.")

def view_transactions():
    phone = simpledialog.askstring("Transactions", "📱 Enter phone number:")
    if phone:
        wallet_id = get_wallet_id(phone)
        if wallet_id:
            c.execute('''SELECT txn_type, amount, timestamp, note FROM Transactions 
                         WHERE sender_wallet = ? OR receiver_wallet = ? ORDER BY timestamp DESC''', (wallet_id, wallet_id))
            transactions = c.fetchall()
            if transactions:
                history = "\n".join([f"{row[2]} - {row[0]} ₹{row[1]} ({row[3]})" for row in transactions])
                messagebox.showinfo("📜 Transaction History", history)
            else:
                messagebox.showinfo("📜 Transaction History", "No transactions found.")
        else:
            messagebox.showerror("⚠️ Error", "Wallet not found.")

# ---------- Update Phone Number ----------
def update_phone_number():
    old_phone = simpledialog.askstring("Update Phone", "📱 Enter current phone number:")
    new_phone = simpledialog.askstring("Update Phone", "📲 Enter new phone number:")

    if old_phone and new_phone:
        c.execute("SELECT * FROM Users WHERE phone = ?", (old_phone,))
        if c.fetchone():
            try:
                c.execute("UPDATE Users SET phone = ? WHERE phone = ?", (new_phone, old_phone))
                conn.commit()
                messagebox.showinfo("✅ Success", f"Phone number updated to {new_phone}!")
            except sqlite3.IntegrityError:
                messagebox.showerror("⚠️ Error", "New phone number already in use.")
        else:
            messagebox.showerror("⚠️ Error", "Old phone number not found.")

# ---------- UI SETUP ----------
root = tk.Tk()
root.title("💳 Digital Wallet System")
root.geometry("420x620")
root.resizable(False, False)
root.configure(bg="#eaf4fc")

# HEADER BAR
header = tk.Label(root, text="💳 Digital Wallet", font=("Helvetica", 20, "bold"), bg="#2980b9", fg="white", pady=10)
header.pack(fill="x")

# Main frame
frame = tk.Frame(root, bg="#eaf4fc")
frame.pack(pady=30)

# Button style
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton",
    font=("Segoe UI", 11),
    padding=10,
    relief="flat",
    background="#3498db",
    foreground="white")
style.map("TButton",
    background=[("active", "#2980b9")],
    foreground=[("disabled", "#ccc")])

# Custom button creator
def fancy_button(text, command):
    btn = ttk.Button(frame, text=text, command=command)
    btn.pack(pady=8, ipadx=8, ipady=5, fill='x', padx=50)

# Buttons
fancy_button("👤 Register User", register_user)
fancy_button("🔁 Update Phone Number", update_phone_number)
fancy_button("➕ Add Money", add_money)
fancy_button("🔁 Transfer Money", transfer_money)
fancy_button("💰 View Balance", view_balance)
fancy_button("📜 View Transactions", view_transactions)
fancy_button("🚪 Exit", root.quit)

# Footer
tk.Label(root, text="© 2025 Digital Wallet Inc.", bg="#eaf4fc", fg="#888", font=("Arial", 9)).pack(side="bottom", pady=10)

root.mainloop()



# python wallet_system.py   
# Shashank Sharma # 6377854949
# Daksh Sood # 7428511405
# Omkar Pote # 9579476397