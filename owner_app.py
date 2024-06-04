import tkinter as tk
from tkinter import messagebox, scrolledtext
import sqlite3
import socket
import threading

# Database Initialization
def initialize_database():
    conn = sqlite3.connect('canteen.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            image TEXT,
            stock INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            product_name TEXT,
            quantity INTEGER,
            total_price REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Populate Database
def populate_database():
    conn = sqlite3.connect('canteen.db')
    cursor = conn.cursor()
    
    # Check if products table is empty before populating
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    if count == 0:
        products = [
            ("Samosa", "Snacks", 10, "images/samosa.jpg", 10),
            ("Sandwich", "Snacks", 30, "images/sandwich.jpg", 10),
            ("Burger", "Snacks", 50, "images/burger.jpg", 10),
            ("Tea", "Beverages", 10, "images/tea.jpg", 10),
            ("Coffee", "Beverages", 20, "images/coffee.jpg", 10),
            ("Juice", "Beverages", 15, "images/juice.jpg", 10),
            ("Lays", "Chips & Chocolates", 20, "images/lays.jpg", 10),
            ("Dairy Milk", "Chips & Chocolates", 30, "images/dairymilk.jpg", 10),
            ("KitKat", "Chips & Chocolates", 25, "images/kitkat.png", 10)
        ]
        
        cursor.executemany('INSERT INTO products (name, category, price, image, stock) VALUES (?, ?, ?, ?, ?)', products)
        conn.commit()

    conn.close()

# Chat Client
class ChatClient(tk.Frame):
    def __init__(self, master, host="localhost", port=9999):
        super().__init__(master)
        self.master = master
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.create_widgets()
        self.connect_to_server()

    def create_widgets(self):
        self.chat_display = scrolledtext.ScrolledText(self, state='disabled', width=50, height=15)
        self.chat_display.pack(pady=10)
        self.chat_display.tag_config('received', foreground='blue')
        self.chat_display.tag_config('sent', foreground='green')
        self.message_entry = tk.Entry(self, width=50)
        self.message_entry.pack(pady=10)
        self.send_button = tk.Button(self, text="Send", command=self.send_message)
        self.send_button.pack(pady=10)

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.host, self.port))
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    self.chat_display.config(state='normal')
                    self.chat_display.insert(tk.END, message + "\n", 'received')
                    self.chat_display.config(state='disabled')
                    self.chat_display.yview(tk.END)
            except:
                break

    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.client_socket.send(f"Owner: {message}".encode())
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, f"Me: {message}\n", 'sent')
            self.chat_display.config(state='disabled')
            self.chat_display.yview(tk.END)
            self.message_entry.delete(0, tk.END)

# Order Management Client
class OrderClient:
    def __init__(self, host="localhost", port=8888):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

    def send_order(self):
        self.client_socket.send("NEW_ORDER".encode())
        return self.client_socket.recv(1024).decode()

    def complete_order(self):
        self.client_socket.send("COMPLETE_ORDER".encode())
        return self.client_socket.recv(1024).decode()

# Main Application for Owner
class OwnerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Canteen Owner Management App")
        self.geometry("800x600")
        self.conn = sqlite3.connect('canteen.db')
        self.order_client = OrderClient()  # Initialize the order client
        self.chat_client = None
        self.create_widgets()

    def create_widgets(self):
        self.order_frame = tk.Frame(self)
        self.order_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_frame = tk.Frame(self)
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_order_section()
        self.create_chat_section()

    def create_order_section(self):
        tk.Label(self.order_frame, text="Orders", font=("Arial", 16)).pack(pady=10)
        self.order_listbox = tk.Listbox(self.order_frame)
        self.order_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.refresh_orders_button = tk.Button(self.order_frame, text="Refresh Orders", command=self.refresh_orders)
        self.refresh_orders_button.pack(pady=5)
        self.complete_order_button = tk.Button(self.order_frame, text="Complete Order", command=self.complete_order)
        self.complete_order_button.pack(pady=5)
        self.refresh_orders()

    def refresh_orders(self):
        self.order_listbox.delete(0, tk.END)
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, product_name, quantity, total_price FROM orders WHERE status = "Pending"')
        orders = cursor.fetchall()
        for order in orders:
            order_text = f"Order ID: {order[0]} - {order[1]} x{order[2]} - ₹{order[3]}"
            self.order_listbox.insert(tk.END, order_text)

    def complete_order(self):
        selected_order = self.order_listbox.get(tk.ACTIVE)
        if selected_order:
            order_id = int(selected_order.split()[2])
            cursor = self.conn.cursor()
            cursor.execute('UPDATE orders SET status = "Completed" WHERE id = ?', (order_id,))
            self.conn.commit()

            # Save the bill as a text file with UTF-8 encoding
            with open(f"bill_{order_id}.txt", "w", encoding="utf-8") as bill_file:
                bill_file.write(f"Order ID: {order_id}\n")
                bill_file.write(selected_order)

            messagebox.showinfo("Order Status", "Order completed successfully and bill saved")
            self.refresh_orders()

    def create_chat_section(self):
        tk.Label(self.chat_frame, text="Chat", font=("Arial", 16)).pack(pady=10)
        self.chat_client = ChatClient(self.chat_frame)
        self.chat_client.pack()

if __name__ == "__main__":
    initialize_database()
    populate_database()
    owner_app = OwnerApp()
    owner_app.mainloop()
