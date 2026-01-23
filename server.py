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


# ---------------------- TCP (legacy) ----------------------
HOST = '0.0.0.0'
DEFAULT_TCP_PORT = 5555

tcp_clients = []
tcp_lock = threading.Lock()


def handle_game_tcp(p1, p2):
    requeued_p1 = False
    requeued_p2 = False

    try:
        while True:
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

            if a1 == "PLAY" and a2 == "PLAY":
                continue

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

            if a1 == "PLAY" and a2 != "PLAY":
                with tcp_lock:
                    tcp_clients.append(p1)
                    requeued_p1 = True
                try:
                    p1.sendall(b"WAIT\n")
                except Exception:
                    requeued_p1 = False

            if a2 == "PLAY" and a1 != "PLAY":
                with tcp_lock:
                    tcp_clients.append(p2)
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


def handle_client_tcp(client):
    try:
        client.sendall(b"WAIT\n")
    except Exception:
        pass

    with tcp_lock:
        tcp_clients.append(client)
        if len(tcp_clients) >= 2:
            p1 = tcp_clients.pop(0)
            p2 = tcp_clients.pop(0)
            threading.Thread(target=handle_game_tcp, args=(p1, p2)).start()


def start_tcp_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    print(f"TCP server running on {host}:{port}...")

    try:
        while True:
            client, addr = server.accept()
            print("Connected:", addr)
            threading.Thread(target=handle_client_tcp, args=(client,)).start()
    finally:
        server.close()


# ---------------------- WebSocket (Cloudflare-friendly) ----------------------
DEFAULT_WS_PORT = 9000

ws_clients = []
ws_lock = None  # will be asyncio.Lock when server starts


async def handle_game_ws(p1, p2):
    requeued_p1 = False
    requeued_p2 = False

    try:
        while True:
            try:
                await p1.send("START")
                await p2.send("START")
            except Exception:
                break

            try:
                c1 = await asyncio.wait_for(p1.recv(), timeout=30)
            except Exception:
                c1 = None

            try:
                c2 = await asyncio.wait_for(p2.recv(), timeout=30)
            except Exception:
                c2 = None

            if not c1 or not c2:
                break

            c1 = c1.strip().upper()
            c2 = c2.strip().upper()

            r1, r2 = determine_winner(c1, c2)

            try:
                await p1.send(r1)
                await p2.send(r2)
            except Exception:
                break

            try:
                await p1.send("PLAY_AGAIN?")
                await p2.send("PLAY_AGAIN?")
            except Exception:
                break

            try:
                a1 = await asyncio.wait_for(p1.recv(), timeout=30)
            except Exception:
                a1 = "QUIT"

            try:
                a2 = await asyncio.wait_for(p2.recv(), timeout=30)
            except Exception:
                a2 = "QUIT"

            a1 = a1.strip().upper() if isinstance(a1, str) else "QUIT"
            a2 = a2.strip().upper() if isinstance(a2, str) else "QUIT"

            if a1 == "PLAY" and a2 == "PLAY":
                continue

            if a1 != "PLAY":
                try:
                    await p1.send("GOODBYE")
                except Exception:
                    pass

            if a2 != "PLAY":
                try:
                    await p2.send("GOODBYE")
                except Exception:
                    pass

            # Requeue remaining players
            if a1 == "PLAY" and a2 != "PLAY":
                async with ws_lock:
                    ws_clients.append(p1)
                    requeued_p1 = True
                try:
                    await p1.send("WAIT")
                except Exception:
                    requeued_p1 = False

            if a2 == "PLAY" and a1 != "PLAY":
                async with ws_lock:
                    ws_clients.append(p2)
                    requeued_p2 = True
                try:
                    await p2.send("WAIT")
                except Exception:
                    requeued_p2 = False

            break
    finally:
        if not requeued_p1:
            try:
                await p1.close()
            except Exception:
                pass

        if not requeued_p2:
            try:
                await p2.close()
            except Exception:
                pass


async def handle_client_ws(websocket, path):
    # Provide a small wrapper to give recv semantics like socket.recv
    class WSWrapper:
        def __init__(self, ws):
            self.ws = ws

        async def send(self, data):
            # ensure sending text
            await self.ws.send(str(data))

        async def recv(self):
            return await self.ws.recv()

        async def close(self):
            await self.ws.close()

    wrapper = WSWrapper(websocket)

    try:
        await websocket.send("WAIT")
    except Exception:
        pass

    async with ws_lock:
        ws_clients.append(wrapper)
        if len(ws_clients) >= 2:
            p1 = ws_clients.pop(0)
            p2 = ws_clients.pop(0)
            # schedule the game
            asyncio.create_task(handle_game_ws(p1, p2))


async def start_ws_server(host, port):
    global ws_lock
    if websockets is None:
        raise RuntimeError("websockets package not installed. Add to requirements.txt and pip install it.")

    ws_lock = asyncio.Lock()
    print(f"WebSocket server running on {host}:{port}...")
    async with websockets.serve(handle_client_ws, host, port):
        await asyncio.Future()  # run forever


def main():
    parser = argparse.ArgumentParser(description="Rock-Paper-Scissors server with TCP and WebSocket modes")
    parser.add_argument('--mode', choices=['tcp', 'ws'], default='tcp', help='Server mode: raw tcp or websocket')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=None)
    args = parser.parse_args()

    if args.mode == 'tcp':
        port = args.port or DEFAULT_TCP_PORT
        start_tcp_server(args.host, port)
    else:
        port = args.port or DEFAULT_WS_PORT
        try:
            asyncio.run(start_ws_server(args.host, port))
        except KeyboardInterrupt:
            print('WebSocket server stopped')


if __name__ == '__main__':
    main()