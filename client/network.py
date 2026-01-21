import socket
import threading

from constants import SERVER_IP, PORT


class ClientNetwork:
    def __init__(self, message_callback):
        self.message_callback = message_callback
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((SERVER_IP, PORT))
        except Exception as e:
            raise ConnectionError(f"Cannot connect to server: {e}")

    def send_choice(self, choice):
        try:
            self.client.sendall((choice + "\n").encode())
        except Exception:
            raise Exception("Failed to send choice to server.")

    def send_play(self):
        try:
            self.client.sendall(b"PLAY\n")
        except Exception:
            pass

    def send_quit(self):
        try:
            self.client.sendall(b"QUIT\n")
        except Exception:
            pass

    def listen_server(self):
        while True:
            try:
                data = self.client.recv(1024)
                if not data:
                    self.message_callback("DISCONNECTED")
                    break

                parts = data.decode().splitlines()
                for part in parts:
                    msg = part.strip()
                    if msg:
                        self.message_callback(msg)
            except Exception:
                break

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass

    def start_listening(self):
        threading.Thread(target=self.listen_server, daemon=True).start()