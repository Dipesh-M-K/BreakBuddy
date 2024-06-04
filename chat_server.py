import socket
import threading

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

if __name__ == "__main__":
    chat_server = ChatServer()
    chat_server.run()
