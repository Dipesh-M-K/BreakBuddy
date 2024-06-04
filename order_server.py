import socket
import threading

class OrderServer:
    def __init__(self, host="localhost", port=8888):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.orders = []
        self.order_counter = 0

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if message.startswith("NEW_ORDER"):
                    self.order_counter += 1
                    self.orders.append(self.order_counter)
                    response = f"Order {self.order_counter} received. {len(self.orders)} orders left."
                    client_socket.send(response.encode())
                elif message.startswith("COMPLETE_ORDER"):
                    if self.orders:
                        completed_order = self.orders.pop(0)
                        response = f"Order {completed_order} completed. {len(self.orders)} orders left."
                        client_socket.send(response.encode())
            except:
                client_socket.close()
                break

    def run(self):
        while True:
            client_socket, addr = self.server.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

if __name__ == "__main__":
    order_server = OrderServer()
    order_server.run()
