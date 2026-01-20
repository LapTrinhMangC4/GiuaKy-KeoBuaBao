import socket
import threading

HOST = '0.0.0.0'
PORT = 5555

clients = []
lock = threading.Lock()

def determine_winner(c1, c2):
    if c1 == c2:
        return "DRAW", "DRAW"

    rules = {
        "ROCK": "SCISSORS",
        "SCISSORS": "PAPER",
        "PAPER": "ROCK"
    }

    if rules[c1] == c2:
        return "WIN", "LOSE"
    return "LOSE", "WIN"

def handle_game(p1, p2):
    try:
        # Bắt đầu ván chơi
        p1.sendall(b"START\n")
        p2.sendall(b"START\n")

        c1 = p1.recv(1024).decode().strip()
        c2 = p2.recv(1024).decode().strip()

        if not c1 or not c2:
            return

        r1, r2 = determine_winner(c1, c2)

        p1.sendall((r1 + "\n").encode())
        p2.sendall((r2 + "\n").encode())

        p1.sendall(b"GOODBYE\n")
        p2.sendall(b"GOODBYE\n")
    finally:
        p1.close()
        p2.close()

def handle_client(client):
    client.sendall(b"WAIT\n")

    with lock:
        clients.append(client)
        if len(clients) >= 2:
            p1 = clients.pop(0)
            p2 = clients.pop(0)
            threading.Thread(
                target=handle_game,
                args=(p1, p2)
            ).start()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("Server running...")

    while True:
        client, addr = server.accept()
        print("Connected:", addr)
        threading.Thread(
            target=handle_client,
            args=(client,)
        ).start()

if __name__ == "__main__":
    start_server()
