import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from PIL import Image, ImageTk, UnidentifiedImageError
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
# Chat Server
class ChatServer:
    def __init__(self, host="localhost", port=9999):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        print(f"Chat server started on {host}:{port}")
        self.clients = []

    def broadcast(self, message, client_socket):
        for client in self.clients:
            if client != client_socket:
                try:
                    client.send(message)
                except:
                    client.close()
                    self.clients.remove(client)

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024)
                if message:
                    print(f"Received: {message.decode()}")
                    self.broadcast(message, client_socket)
            except:
                client_socket.close()
                self.clients.remove(client_socket)
                break

    def run(self):
        while True:
            client_socket, addr = self.server.accept()
            self.clients.append(client_socket)
            print(f"Client connected from {addr}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

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
        self.send_button = tk.Button(self, text="Send", command=self.send_message, bg="#4CAF50", fg="white")
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
            self.client_socket.send(f"Customer: {message}".encode())
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, f"Me: {message}\n", 'sent')
            self.chat_display.config(state='disabled')
            self.chat_display.yview(tk.END)
            self.message_entry.delete(0, tk.END)

# Order Client
class OrderClient:
    def __init__(self, host="localhost", port=8888):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

    def send_order(self, order_details):
        self.client_socket.send(f"NEW_ORDER {order_details}".encode())
        return self.client_socket.recv(1024).decode()

    def complete_order(self):
        self.client_socket.send("COMPLETE_ORDER".encode())
        return self.client_socket.recv(1024).decode()

# Main Application
class RestaurantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Restaurant Management App")
        self.geometry("1000x600")
        self.conn = sqlite3.connect('canteen.db')
        self.create_menu()
        self.create_widgets()
        self.order_items = []
        self.order_client = OrderClient()  # Initialize the order client
        self.chat_client = None
        self.discount = 0  # Initialize discount

    def create_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        chatmenu = tk.Menu(menubar, tearoff=0)
        chatmenu.add_command(label="Open Chat", command=self.open_chat)
        menubar.add_cascade(label="Chat", menu=chatmenu)        
        self.config(menu=menubar)

    def create_widgets(self):
        self.category_frame = tk.Frame(self, bg="#f0f0f0")
        self.category_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.product_frame = tk.Frame(self, bg="#ffffff")
        self.product_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.order_frame = tk.Frame(self, bg="#f0f0f0")
        self.order_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.create_category_buttons()
        self.create_order_section()

    def create_category_buttons(self):
        tk.Label(self.category_frame, text="Categories", font=("Arial", 16), bg="#f0f0f0").pack(pady=10)
        categories = ["All Products"] + self.get_categories()
        for category in categories:
            button = tk.Button(self.category_frame, text=category, command=lambda c=category: self.show_products(c), bg="#4CAF50", fg="white")
            button.pack(fill=tk.X, pady=5, padx=10)

    def get_categories(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM products')
        categories = [row[0] for row in cursor.fetchall()]
        return categories

    def show_products(self, category):
        for widget in self.product_frame.winfo_children():
            widget.destroy()

        cursor = self.conn.cursor()
        if category == "All Products":
            cursor.execute('SELECT name, price, image, stock FROM products')
        else:
            cursor.execute('SELECT name, price, image, stock FROM products WHERE category = ?', (category,))

        self.product_images = {}
        canvas = tk.Canvas(self.product_frame, bg="#ffffff")
        scrollbar = ttk.Scrollbar(self.product_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row = 0
        column = 0

        for name, price, image_path, stock in cursor.fetchall():
            if stock > 0:
                try:
                    img = Image.open(image_path)
                    img = img.resize((150, 150), Image.Resampling.LANCZOS)
                    img = ImageTk.PhotoImage(img)
                    self.product_images[name] = img
                except UnidentifiedImageError as e:
                    print(f"Error loading image {image_path}: {e}")
                    img = ImageTk.PhotoImage(Image.new("RGB", (150, 150), "white"))
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    img = ImageTk.PhotoImage(Image.new("RGB", (150, 150), "white"))

                frame = tk.Frame(scrollable_frame, bg="#ffffff", bd=1, relief="solid")
                frame.grid(row=row, column=column, padx=10, pady=10)
                
                button = tk.Button(
                    frame,
                    text=f"{name}\n(₹{price})",
                    image=img,
                    compound=tk.TOP,
                    width=150,
                    height=200,
                    command=lambda p=name, pr=price: self.add_to_order(p, pr)
                )
                button.pack()

                column += 1
                if column > 2:
                    column = 0
                    row += 1

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_order_section(self):
        tk.Label(self.order_frame, text="Order", font=("Arial", 16), bg="#f0f0f0").pack(pady=10)
        self.order_listbox = tk.Listbox(self.order_frame)
        self.order_listbox.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        self.total_label = tk.Label(self.order_frame, text="Total: ₹0", font=("Arial", 14), bg="#f0f0f0")
        self.total_label.pack(pady=10)
        tk.Button(self.order_frame, text="Place Order", command=self.place_order, bg="#4CAF50", fg="white").pack(pady=5, padx=10)
        tk.Button(self.order_frame, text="Clear Order", command=self.clear_order, bg="#4CAF50", fg="white").pack(pady=5, padx=10)
        tk.Button(self.order_frame, text="Apply Discount", command=self.apply_discount, bg="#4CAF50", fg="white").pack(pady=5, padx=10)

    def add_to_order(self, product, price):
        quantity = 1
        order_entry = f"{product} x{quantity} - ₹{price * quantity}"
        self.order_items.append((product, price, quantity))
        self.order_listbox.insert(tk.END, order_entry)
        self.update_total()

    def update_total(self):
        total = sum(price * quantity for product, price, quantity in self.order_items)
        discounted_total = total - (total * self.discount / 100)
        self.total_label.config(text=f"Total: ₹{discounted_total:.2f} (Discount: {self.discount}%)")

    def clear_order(self):
        self.order_items.clear()
        self.order_listbox.delete(0, tk.END)
        self.update_total()

    def apply_discount(self):
        self.discount = 10  # Example: Apply a flat 10% discount
        self.update_total()

    def place_order(self):
        if not self.order_items:
            messagebox.showerror("Error", "No items in the order.")
            return

        conn = sqlite3.connect('canteen.db')
        cursor = conn.cursor()

        for product, price, quantity in self.order_items:
            total_price = price * quantity
            cursor.execute('''
                INSERT INTO orders (product_name, quantity, total_price, status)
                VALUES (?, ?, ?, ?)
            ''', (product, quantity, total_price, "Pending"))

        conn.commit()
        conn.close()

        messagebox.showinfo("Order Placed", "Your order has been placed successfully.")
        self.clear_order()

    def open_chat(self):
        chat_window = tk.Toplevel(self)
        chat_window.title("Chat")
        self.chat_client = ChatClient(chat_window)
        self.chat_client.pack()

if __name__ == "__main__":
    initialize_database()
    populate_database()
    app = RestaurantApp()
    app.mainloop()
