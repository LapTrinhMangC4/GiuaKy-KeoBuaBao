import socket
import threading
import tkinter as tk
from tkinter import messagebox

SERVER_IP = "127.0.0.1"
PORT = 5555


class RPSClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors")
        self.root.geometry("350x300")

        # ensure proper cleanup when user clicks the window X
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((SERVER_IP, PORT))
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {e}")
            root.destroy()
            return

        # top status frame
        self.top_frame = tk.Frame(root, bg="#2c3e50")
        self.top_frame.pack(fill="x")

        self.title_label = tk.Label(self.top_frame, text="Rock Paper Scissors", bg="#2c3e50", fg="white", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=10)

        self.status_label = tk.Label(root, text="Waiting for opponent...", font=("Arial", 12), fg="#34495e")
        self.status_label.pack(pady=8)

        # result label
        self.result_label = tk.Label(root, text="", font=("Arial", 12), fg="#16a085")
        self.result_label.pack(pady=4)

        # buttons frame
        self.frame = tk.Frame(root)
        self.frame.pack(pady=10)

        btn_style = {"width": 12, "height": 2, "bg": "#ecf0f1", "fg": "#2c3e50", "font": ("Arial", 10, "bold")}

        self.btn_rock = tk.Button(self.frame, text="ROCK", command=lambda: self.send_choice("ROCK"), **btn_style)
        self.btn_paper = tk.Button(self.frame, text="PAPER", command=lambda: self.send_choice("PAPER"), **btn_style)
        self.btn_scissors = tk.Button(self.frame, text="SCISSORS", command=lambda: self.send_choice("SCISSORS"), **btn_style)

        self.btn_rock.grid(row=0, column=0, padx=6)
        self.btn_paper.grid(row=0, column=1, padx=6)
        self.btn_scissors.grid(row=0, column=2, padx=6)

        # play again / quit frame (hidden until needed)
        self.rematch_frame = tk.Frame(root)
        self.btn_play_again = tk.Button(self.rematch_frame, text="Play Again", width=12, height=1, bg="#27ae60", fg="white", command=self.send_play)
        self.btn_quit = tk.Button(self.rematch_frame, text="Quit", width=12, height=1, bg="#c0392b", fg="white", command=self.send_quit)
        self.btn_play_again.pack(side="left", padx=8)
        self.btn_quit.pack(side="left", padx=8)

        self.disable_buttons()

        threading.Thread(target=self.listen_server, daemon=True).start()

    def disable_buttons(self):
        self.btn_rock.config(state="disabled")
        self.btn_paper.config(state="disabled")
        self.btn_scissors.config(state="disabled")
        # hide rematch frame until asked
        try:
            self.rematch_frame.pack_forget()
        except Exception:
            pass

    def enable_buttons(self):
        self.btn_rock.config(state="normal")
        self.btn_paper.config(state="normal")
        self.btn_scissors.config(state="normal")

    def send_choice(self, choice):
        try:
            self.client.sendall((choice + "\n").encode())
        except Exception:
            # if send fails, notify user
            self.root.after(0, lambda: messagebox.showerror("Error", "Failed to send choice to server."))
            return
        self.disable_buttons()
        self.status_label.config(text=f"You chose {choice}")

    def _handle_msg(self, msg):
        if msg == "WAIT":
            self.status_label.config(text="Waiting for opponent...")
            self.result_label.config(text="")
            # ensure buttons are disabled and rematch options hidden when requeued
            self.disable_buttons()
            try:
                if self.rematch_frame.winfo_ismapped():
                    self.rematch_frame.pack_forget()
            except Exception:
                pass
        elif msg == "START":
            self.status_label.config(text="Choose your move")
            self.result_label.config(text="")
            self.enable_buttons()
            # hide rematch options when a new round starts
            try:
                if self.rematch_frame.winfo_ismapped():
                    self.rematch_frame.pack_forget()
            except Exception:
                pass
        elif msg in ["WIN", "LOSE", "DRAW"]:
            self.result_label.config(text=f"Result: {msg}")
            messagebox.showinfo("Game Result", msg)
            # after showing result, wait for server's PLAY_AGAIN? prompt
        elif msg == "PLAY_AGAIN?":
            # show play again / quit options (avoid packing multiple times)
            try:
                if not self.rematch_frame.winfo_ismapped():
                    self.rematch_frame.pack(pady=8)
            except Exception:
                try:
                    self.rematch_frame.pack(pady=8)
                except Exception:
                    pass
        elif msg == "GOODBYE":
            messagebox.showinfo("Server", "Opponent left the game. Connection will close.")
            try:
                self.client.close()
            except Exception:
                pass
            self.disable_buttons()
            self.status_label.config(text="Disconnected")

    def listen_server(self):
        while True:
            try:
                data = self.client.recv(1024)
                if not data:
                    # connection closed
                    self.root.after(0, lambda: self.status_label.config(text="Disconnected from server"))
                    try:
                        self.client.close()
                    except Exception:
                        pass
                    break

                # handle possible multiple messages separated by newline
                parts = data.decode().splitlines()
                for part in parts:
                    msg = part.strip()
                    if not msg:
                        continue
                    # schedule UI updates on main thread
                    self.root.after(0, self._handle_msg, msg)
            except Exception:
                break

    def send_play(self):
        try:
            self.client.sendall(b"PLAY\n")
        except Exception:
            pass
        # hide rematch options until asked again
        try:
            self.rematch_frame.pack_forget()
        except Exception:
            pass

    def send_quit(self):
        # user-initiated quit: notify server, close socket, and destroy window
        try:
            self.client.sendall(b"QUIT\n")
        except Exception:
            pass
        try:
            self.client.close()
        except Exception:
            pass
        self.disable_buttons()
        self.status_label.config(text="You left the game")
        try:
            self.root.destroy()
        except Exception:
            pass

    def on_closing(self):
        # same behavior as clicking Quit
        self.send_quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()
import socket
import threading
import tkinter as tk
from tkinter import messagebox

SERVER_IP = "127.0.0.1"
PORT = 5555

class RPSClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors")
        self.root.geometry("350x300")

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((SERVER_IP, PORT))

        self.label = tk.Label(root, text="Waiting for opponent...", font=("Arial", 14))
        self.label.pack(pady=20)

        self.frame = tk.Frame(root)
        self.frame.pack()

        self.btn_rock = tk.Button(self.frame, text="ROCK", width=10,
                                  command=lambda: self.send_choice("ROCK"))
        self.btn_paper = tk.Button(self.frame, text="PAPER", width=10,
                                   command=lambda: self.send_choice("PAPER"))
        self.btn_scissors = tk.Button(self.frame, text="SCISSORS", width=10,
                                      command=lambda: self.send_choice("SCISSORS"))

        self.btn_rock.grid(row=0, column=0, padx=5)
        self.btn_paper.grid(row=0, column=1, padx=5)
        self.btn_scissors.grid(row=0, column=2, padx=5)

        self.disable_buttons()

        threading.Thread(target=self.listen_server, daemon=True).start()

    def disable_buttons(self):
        self.btn_rock.config(state="disabled")
        self.btn_paper.config(state="disabled")
        self.btn_scissors.config(state="disabled")

    def enable_buttons(self):
        self.btn_rock.config(state="normal")
        self.btn_paper.config(state="normal")
        self.btn_scissors.config(state="normal")

    def send_choice(self, choice):
        self.client.sendall((choice + "\n").encode())
        self.disable_buttons()
        self.label.config(text=f"You chose {choice}")

    def listen_server(self):
        while True:
            try:
                msg = self.client.recv(1024).decode().strip()

                if msg == "WAIT":
                    self.label.config(text="Waiting for opponent...")
                elif msg == "START":
                    self.label.config(text="Choose your move")
                    self.enable_buttons()
                elif msg in ["WIN", "LOSE", "DRAW"]:
                    self.label.config(text=f"Result: {msg}")
                    messagebox.showinfo("Game Result", msg)
                    self.client.close()
                    break
            except:
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()
import socket
import threading
import tkinter as tk
from tkinter import messagebox

SERVER_IP = "127.0.0.1"
PORT = 5555

class RPSClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors")
        self.root.geometry("350x300")

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((SERVER_IP, PORT))

        self.label = tk.Label(root, text="Waiting for opponent...", font=("Arial", 14))
        self.label.pack(pady=20)

        self.frame = tk.Frame(root)
        self.frame.pack()

        self.btn_rock = tk.Button(self.frame, text="ROCK", width=10,
                                  command=lambda: self.send_choice("ROCK"))
        self.btn_paper = tk.Button(self.frame, text="PAPER", width=10,
                                   command=lambda: self.send_choice("PAPER"))
        self.btn_scissors = tk.Button(self.frame, text="SCISSORS", width=10,
                                      command=lambda: self.send_choice("SCISSORS"))

        self.btn_rock.grid(row=0, column=0, padx=5)
        self.btn_paper.grid(row=0, column=1, padx=5)
        self.btn_scissors.grid(row=0, column=2, padx=5)

        self.disable_buttons()

        threading.Thread(target=self.listen_server, daemon=True).start()

    def disable_buttons(self):
        self.btn_rock.config(state="disabled")
        self.btn_paper.config(state="disabled")
        self.btn_scissors.config(state="disabled")

    def enable_buttons(self):
        self.btn_rock.config(state="normal")
        self.btn_paper.config(state="normal")
        self.btn_scissors.config(state="normal")

    def send_choice(self, choice):
        self.client.sendall((choice + "\n").encode())
        self.disable_buttons()
        self.label.config(text=f"You chose {choice}")

    def listen_server(self):
        while True:
            try:
                msg = self.client.recv(1024).decode().strip()

                if msg == "WAIT":
                    self.label.config(text="Waiting for opponent...")
                elif msg == "START":
                    self.label.config(text="Choose your move")
                    self.enable_buttons()
                elif msg in ["WIN", "LOSE", "DRAW"]:
                    self.label.config(text=f"Result: {msg}")
                    messagebox.showinfo("Game Result", msg)
                    self.client.close()
                    break
            except:
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()
