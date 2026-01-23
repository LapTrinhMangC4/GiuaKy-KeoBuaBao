import tkinter as tk
from tkinter import messagebox
import threading
import asyncio
import websockets

WS_URL = "wss://bolt-extensions-stamp-flooring.trycloudflare.com"


class RPSClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Rock Paper Scissors")
        self.root.geometry("500x600")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.ws = None
        self.loop = asyncio.new_event_loop()

        header = tk.Label(root, text="✊ ✋ ✌️", font=("Segoe UI Emoji", 40), bg="#1a1a2e", fg="#e94560")
        header.pack(pady=10)

        self.status = tk.Label(root, text="Connecting...", font=("Arial", 14), bg="#1a1a2e", fg="white")
        self.status.pack(pady=10)

        self.result = tk.Label(root, text="", font=("Arial", 16, "bold"), bg="#1a1a2e")
        self.result.pack(pady=10)

        btn_frame = tk.Frame(root, bg="#1a1a2e")
        btn_frame.pack(pady=30)

        self.buttons = {}
        for choice in ["ROCK", "PAPER", "SCISSORS"]:
            b = tk.Button(
                btn_frame,
                text=choice,
                font=("Arial", 12, "bold"),
                width=10,
                height=2,
                command=lambda c=choice: self.send(c)
            )
            b.pack(side="left", padx=10)
            self.buttons[choice] = b

        self.rematch = tk.Button(
            root, text="🔄 Play Again", font=("Arial", 12, "bold"),
            command=lambda: self.send("PLAY")
        )

        threading.Thread(target=self.start_ws, daemon=True).start()
        self.disable_buttons()

    def start_ws(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    async def connect(self):
        try:
            self.ws = await websockets.connect(WS_URL)
            self.root.after(0, lambda: self.status.config(text="Connected. Waiting for opponent..."))
            await self.listen()
        except Exception:
            self.root.after(0, lambda: messagebox.showerror("Error", "Cannot connect to server"))

    async def listen(self):
        try:
            async for msg in self.ws:
                self.root.after(0, self.handle_msg, msg)
        except:
            pass

    def handle_msg(self, msg):
        if msg == "WAIT":
            self.status.config(text="Waiting for opponent...")
            self.disable_buttons()
            self.rematch.pack_forget()

        elif msg == "START":
            self.status.config(text="Choose your move!")
            self.result.config(text="")
            self.enable_buttons()
            self.rematch.pack_forget()

        elif msg == "WIN":
            self.result.config(text="🎉 YOU WIN!", fg="#00ff88")

        elif msg == "LOSE":
            self.result.config(text="😔 YOU LOSE", fg="#e94560")

        elif msg == "DRAW":
            self.result.config(text="🤝 DRAW", fg="#f39c12")

        elif msg == "PLAY_AGAIN?":
            self.rematch.pack(pady=15)

        elif msg == "GOODBYE":
            messagebox.showinfo("Info", "Opponent left")
            self.root.destroy()

    def send(self, msg):
        self.disable_buttons()
        asyncio.run_coroutine_threadsafe(self.ws.send(msg), self.loop)

    def disable_buttons(self):
        for b in self.buttons.values():
            b.config(state="disabled")

    def enable_buttons(self):
        for b in self.buttons.values():
            b.config(state="normal")

    def on_closing(self):
        try:
            asyncio.run_coroutine_threadsafe(self.ws.send("QUIT"), self.loop)
        except:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()
