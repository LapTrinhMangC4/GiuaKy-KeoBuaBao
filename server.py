import argparse
import socket
import threading
import asyncio

try:
    import websockets
except Exception:
    websockets = None


def determine_winner(c1, c2):
    if c1 == c2:
        return "DRAW", "DRAW"

    rules = {
        "ROCK": "SCISSORS",
        "SCISSORS": "PAPER",
        "PAPER": "ROCK"
    }

    if rules.get(c1) == c2:
        return "WIN", "LOSE"
    return "LOSE", "WIN"


# ====================== TCP (GIỮ NGUYÊN) ======================
HOST = '0.0.0.0'
DEFAULT_TCP_PORT = 5555

tcp_clients = []
tcp_lock = threading.Lock()


def handle_game_tcp(p1, p2):
    try:
        while True:
            p1.sendall(b"START\n")
            p2.sendall(b"START\n")

            c1 = p1.recv(1024).decode().strip()
            c2 = p2.recv(1024).decode().strip()

            r1, r2 = determine_winner(c1, c2)

            p1.sendall((r1 + "\n").encode())
            p2.sendall((r2 + "\n").encode())

            p1.sendall(b"PLAY_AGAIN?\n")
            p2.sendall(b"PLAY_AGAIN?\n")

            a1 = p1.recv(1024).decode().strip()
            a2 = p2.recv(1024).decode().strip()

            if a1 == "PLAY" and a2 == "PLAY":
                continue
            break
    finally:
        p1.close()
        p2.close()


def handle_client_tcp(client):
    client.sendall(b"WAIT\n")

    with tcp_lock:
        tcp_clients.append(client)
        if len(tcp_clients) >= 2:
            p1 = tcp_clients.pop(0)
            p2 = tcp_clients.pop(0)
            threading.Thread(target=handle_game_tcp, args=(p1, p2)).start()


def start_tcp_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"TCP server running on {host}:{port}")

    while True:
        client, _ = server.accept()
        threading.Thread(target=handle_client_tcp, args=(client,)).start()


# ====================== WEBSOCKET (FIX) ======================
DEFAULT_WS_PORT = 9100

ws_clients = []
ws_lock = None


async def handle_game_ws(p1, p2):
    try:
        while True:
            await p1.send("START")
            await p2.send("START")

            c1 = (await asyncio.wait_for(p1.recv(), 30)).strip().upper()
            c2 = (await asyncio.wait_for(p2.recv(), 30)).strip().upper()

            r1, r2 = determine_winner(c1, c2)

            await p1.send(r1)
            await p2.send(r2)

            await p1.send("PLAY_AGAIN?")
            await p2.send("PLAY_AGAIN?")

            a1 = (await asyncio.wait_for(p1.recv(), 30)).strip().upper()
            a2 = (await asyncio.wait_for(p2.recv(), 30)).strip().upper()

            if a1 == "PLAY" and a2 == "PLAY":
                continue

            if a1 != "PLAY":
                await p1.send("GOODBYE")
                await p1.close()

            if a2 != "PLAY":
                await p2.send("GOODBYE")
                await p2.close()

            if a1 == "PLAY" and a2 != "PLAY":
                async with ws_lock:
                    ws_clients.append(p1)
                await p1.send("WAIT")

            if a2 == "PLAY" and a1 != "PLAY":
                async with ws_lock:
                    ws_clients.append(p2)
                await p2.send("WAIT")

            break
    except:
        pass


async def handle_client_ws(websocket, path=None):
    try:
        await websocket.send("WAIT")
    except:
        return

    async with ws_lock:
        ws_clients.append(websocket)

        if len(ws_clients) >= 2:
            p1 = ws_clients.pop(0)
            p2 = ws_clients.pop(0)
            asyncio.create_task(handle_game_ws(p1, p2))


async def start_ws_server(host, port):
    global ws_lock
    ws_lock = asyncio.Lock()

    print(f"WebSocket server running on {host}:{port}")
    async with websockets.serve(handle_client_ws, host, port):
        await asyncio.Future()  # run forever


# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['tcp', 'ws'], default='tcp')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int)
    args = parser.parse_args()

    if args.mode == 'tcp':
        start_tcp_server(args.host, args.port or DEFAULT_TCP_PORT)
    else:
        asyncio.run(start_ws_server(args.host, args.port or DEFAULT_WS_PORT))


if __name__ == "__main__":
    main()
