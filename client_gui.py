import socket
import threading
import tkinter as tk
from tkinter import messagebox

SERVER_IP = "127.0.0.1"
PORT = 5555


class RPSClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Rock Paper Scissors")
        self.root.geometry("500x600")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        # ensure proper cleanup when user clicks the window X
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.retry_button = None

        # Header
        header_frame = tk.Frame(root, bg="#16213e", height=100)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(
            header_frame, 
            text="✊ ✋ ✌️",
            font=("Segoe UI Emoji", 36),
            bg="#16213e",
            fg="#e94560"
        )
        title_label.pack(pady=(10, 0))
        
        subtitle_label = tk.Label(
            header_frame,
            text="ROCK PAPER SCISSORS",
            font=("Arial", 18, "bold"),
            bg="#16213e",
            fg="#ffffff"
        )
        subtitle_label.pack(pady=(0, 10))

        # Status container
        status_container = tk.Frame(root, bg="#0f3460", bd=0)
        status_container.pack(pady=20, padx=40, fill="x")
        
        self.status_label = tk.Label(
            status_container,
            text="Waiting for opponent...",
            font=("Arial", 14),
            bg="#0f3460",
            fg="#ffffff",
            pady=15
        )
        self.status_label.pack()

        # Result label with animation-ready styling
        self.result_label = tk.Label(
            root,
            text="",
            font=("Arial", 16, "bold"),
            bg="#1a1a2e",
            fg="#00ff88",
            pady=10
        )
        self.result_label.pack()

        # Game buttons frame
        buttons_frame = tk.Frame(root, bg="#1a1a2e")
        buttons_frame.pack(pady=30)

        # Button styling
        btn_configs = {
            "ROCK": {"emoji": "✊", "color": "#e94560", "hover": "#d63651"},
            "PAPER": {"emoji": "✋", "color": "#4a90e2", "hover": "#3a7bc8"},
            "SCISSORS": {"emoji": "✌️", "color": "#f39c12", "hover": "#da8c0f"}
        }

        self.buttons = {}
        for idx, (choice, config) in enumerate(btn_configs.items()):
            btn_frame = tk.Frame(buttons_frame, bg=config["color"], bd=0)
            btn_frame.grid(row=0, column=idx, padx=15)
            
            # Emoji label
            emoji_label = tk.Label(
                btn_frame,
                text=config["emoji"],
                font=("Segoe UI Emoji", 48),
                bg=config["color"],
                fg="#ffffff"
            )
            emoji_label.pack(pady=(15, 5))
            
            # Choice button
            btn = tk.Button(
                btn_frame,
                text=choice,
                font=("Arial", 12, "bold"),
                bg=config["color"],
                fg="#ffffff",
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda c=choice: self.send_choice(c),
                activebackground=config["hover"],
                activeforeground="#ffffff"
            )
            btn.pack(pady=(0, 15))
            
            self.buttons[choice] = {"btn": btn, "frame": btn_frame, "config": config}
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn, cfg=config: b.config(bg=cfg["hover"]))
            btn.bind("<Leave>", lambda e, b=btn, cfg=config: b.config(bg=cfg["color"]))

        # Rematch frame
        self.rematch_frame = tk.Frame(root, bg="#1a1a2e")
        
        rematch_btn_frame = tk.Frame(self.rematch_frame, bg="#1a1a2e")
        rematch_btn_frame.pack(pady=10)
        
        self.btn_play_again = tk.Button(
            rematch_btn_frame,
            text="🔄 Play Again",
            font=("Arial", 12, "bold"),
            bg="#00d9ff",
            fg="#1a1a2e",
            bd=0,
            padx=25,
            pady=12,
            cursor="hand2",
            command=self.send_play,
            activebackground="#00b8d4"
        )
        self.btn_play_again.pack(side="left", padx=10)
        
        self.btn_quit = tk.Button(
            rematch_btn_frame,
            text="❌ Quit",
            font=("Arial", 12, "bold"),
            bg="#e94560",
            fg="#ffffff",
            bd=0,
            padx=25,
            pady=12,
            cursor="hand2",
            command=self.send_quit,
            activebackground="#d63651"
        )
        self.btn_quit.pack(side="left", padx=10)

        # Footer
        footer_label = tk.Label(
            root,
            text="Good luck! 🍀",
            font=("Arial", 10),
            bg="#1a1a2e",
            fg="#888888"
        )
        footer_label.pack(side="bottom", pady=20)

        self.connect_to_server()
        self.disable_buttons()

    def connect_to_server(self):
        try:
            self.client.connect((SERVER_IP, PORT))
            self.connected = True
            self.status_label.config(text="Connected! Waiting for opponent...")
            if self.retry_button:
                self.retry_button.pack_forget()
                self.retry_button = None
            threading.Thread(target=self.listen_server, daemon=True).start()
        except Exception as e:
            self.connected = False
            self.status_label.config(text="Cannot connect to server. Click Retry to try again.")
            if not self.retry_button:
                self.retry_button = tk.Button(
                    self.status_container,
                    text="🔄 Retry Connection",
                    font=("Arial", 12, "bold"),
                    bg="#e94560",
                    fg="#ffffff",
                    bd=0,
                    padx=20,
                    pady=10,
                    cursor="hand2",
                    command=self.connect_to_server
                )
                self.retry_button.pack(pady=10)

    def disable_buttons(self):
        for choice_data in self.buttons.values():
            choice_data["btn"].config(state="disabled", cursor="arrow")
        try:
            self.rematch_frame.pack_forget()
        except Exception:
            pass

    def enable_buttons(self):
        for choice_data in self.buttons.values():
            choice_data["btn"].config(state="normal", cursor="hand2")

    def send_choice(self, choice):
        if not self.connected:
            return
        try:
            self.client.sendall((choice + "\n").encode())
        except Exception:
            self.root.after(0, lambda: messagebox.showerror("Error", "Failed to send choice to server."))
            return
        self.disable_buttons()
        self.status_label.config(text=f"You chose {choice} ⏳")

    def _handle_msg(self, msg):
        if msg == "WAIT":
            self.status_label.config(text="Waiting for opponent... ⏳")
            self.result_label.config(text="")
            self.disable_buttons()
            try:
                if self.rematch_frame.winfo_ismapped():
                    self.rematch_frame.pack_forget()
            except Exception:
                pass
        elif msg == "START":
            self.status_label.config(text="Choose your move! 🎯")
            self.result_label.config(text="")
            self.enable_buttons()
            try:
                if self.rematch_frame.winfo_ismapped():
                    self.rematch_frame.pack_forget()
            except Exception:
                pass
        elif msg == "WIN":
            self.result_label.config(text="🎉 YOU WIN! 🎉", fg="#00ff88")
            messagebox.showinfo("Game Result", "Congratulations! You won! 🏆")
        elif msg == "LOSE":
            self.result_label.config(text="😔 YOU LOSE", fg="#e94560")
            messagebox.showinfo("Game Result", "Better luck next time! 💪")
        elif msg == "DRAW":
            self.result_label.config(text="🤝 IT'S A DRAW!", fg="#f39c12")
            messagebox.showinfo("Game Result", "It's a tie! Try again! 🔄")
        elif msg == "PLAY_AGAIN?":
            try:
                if not self.rematch_frame.winfo_ismapped():
                    self.rematch_frame.pack(pady=20)
            except Exception:
                try:
                    self.rematch_frame.pack(pady=20)
                except Exception:
                    pass
        elif msg == "GOODBYE":
            messagebox.showinfo("Server", "Opponent left the game. Connection will close. 👋")
            try:
                self.client.close()
            except Exception:
                pass
            self.disable_buttons()
            self.status_label.config(text="Disconnected ❌")

    def listen_server(self):
        while True:
            try:
                data = self.client.recv(1024)
                if not data:
                    self.root.after(0, lambda: self.status_label.config(text="Disconnected from server ❌"))
                    try:
                        self.client.close()
                    except Exception:
                        pass
                    break

                parts = data.decode().splitlines()
                for part in parts:
                    msg = part.strip()
                    if not msg:
                        continue
                    self.root.after(0, self._handle_msg, msg)
            except Exception:
                break

    def send_play(self):
        if not self.connected:
            return
        try:
            self.client.sendall(b"PLAY\n")
        except Exception:
            pass
        try:
            self.rematch_frame.pack_forget()
        except Exception:
            pass

    def send_quit(self):
        try:
            self.client.sendall(b"QUIT\n")
        except Exception:
            pass
        try:
            self.client.close()
        except Exception:
            pass
        self.disable_buttons()
        self.status_label.config(text="You left the game 👋")
        try:
            self.root.destroy()
        except Exception:
            pass

    def on_closing(self):
        self.send_quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()