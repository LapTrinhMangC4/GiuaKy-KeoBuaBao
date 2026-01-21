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
    requeued_p1 = False
    requeued_p2 = False

    try:
        while True:
            # Bắt đầu ván chơi
            try:
                p1.sendall(b"START\n")
                p2.sendall(b"START\n")
            except Exception:
                break

            try:
                c1 = p1.recv(1024).decode().strip()
            except Exception:
                c1 = None

            try:
                c2 = p2.recv(1024).decode().strip()
            except Exception:
                c2 = None

            if not c1 or not c2:
                break

            r1, r2 = determine_winner(c1, c2)

            try:
                p1.sendall((r1 + "\n").encode())
                p2.sendall((r2 + "\n").encode())
            except Exception:
                break

            # Hỏi chơi lại
            try:
                p1.sendall(b"PLAY_AGAIN?\n")
                p2.sendall(b"PLAY_AGAIN?\n")
            except Exception:
                break

            try:
                a1 = p1.recv(1024).decode().strip()
            except Exception:
                a1 = "QUIT"

            try:
                a2 = p2.recv(1024).decode().strip()
            except Exception:
                a2 = "QUIT"

            # Cả hai muốn chơi tiếp
            if a1 == "PLAY" and a2 == "PLAY":
                continue

            # Gửi goodbye
            if a1 != "PLAY":
                try:
                    p1.sendall(b"GOODBYE\n")
                except Exception:
                    pass

            if a2 != "PLAY":
                try:
                    p2.sendall(b"GOODBYE\n")
                except Exception:
                    pass

            # Requeue người còn chơi
            if a1 == "PLAY" and a2 != "PLAY":
                with lock:
                    clients.append(p1)
                    requeued_p1 = True
                try:
                    p1.sendall(b"WAIT\n")
                except Exception:
                    requeued_p1 = False

            if a2 == "PLAY" and a1 != "PLAY":
                with lock:
                    clients.append(p2)
                    requeued_p2 = True
                try:
                    p2.sendall(b"WAIT\n")
                except Exception:
                    requeued_p2 = False

            break
    finally:
        if not requeued_p1:
            try:
                p1.close()
            except Exception:
                pass

        if not requeued_p2:
            try:
                p2.close()
            except Exception:
                pass

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