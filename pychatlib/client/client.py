import socket
import json
from threading import Thread
from random import choice
from tkinter import *

from .networking import receive, send_message, send_command
from .config import THEMES, USERNAME

class Client:
    def __init__(self):
        self.JOIN_MESSAGES = ["just joined!", "has joined", "has entered the chat", "arrived!", "slid in!", "showed up!", "joined the party!"]
        self.LEAVE_MESSAGES = ["left the chat", "has left", "just left", "has exited", "flew away!"]
        self.theme = THEMES["sweden"]
        self.system_message_indexes = []

        self.init_gui()
        self.init_socket()
        self.gui_mainloop()

    def init_gui(self):
        self.root = Tk()
        self.root.title("PyChat4")
        self.root.geometry("600x350")

        self.root.tk_setPalette(background=self.theme["bg"], foreground=self.theme["fg"],
               activeBackground=self.theme["bg2"], activeForeground=self.theme["fg"])

        self.messages = Listbox(width=90, height=10, font=("", 11), bg=self.theme["bg2"], selectbackground=self.theme["bg2"], selectforeground=self.theme["fg"])
        self.messages.pack(pady=(25,15))
        self.insert_system_message("Welcome to PyChat!")

        self.messagebox_var = StringVar()
        self.messagebox = Entry(textvariable=self.messagebox_var, width=25, font=("", 11))
        self.messagebox.pack()

        self.send_message_button = Button(text="Send", font=("", 12), command=self.send, bg=self.theme["bg2"])
        self.send_message_button.pack(pady=(5, 5))

    def set_gui_theme(self):
        self.root.tk_setPalette(background=self.theme["bg"], foreground=self.theme["fg"],
               activeBackground=self.theme["bg2"], activeForeground=self.theme["fg"])
        
        self.messages.config(bg=self.theme["bg2"], selectbackground=self.theme["bg2"], selectforeground=self.theme["fg"])
        self.send_message_button.config(bg=self.theme["bg2"])

        for i in self.system_message_indexes:
            self.messages.itemconfig(i, {"fg": self.theme["fg_highlight"], "selectforeground": self.theme["fg_highlight"]})

    def gui_mainloop(self):
        self.root.mainloop()

    def init_socket(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("0.0.0.0", 5555))

        thread = Thread(target=self.receive_loop, daemon=True)
        thread.start()

        send_command(self.s, {"command": "set_username", "username": USERNAME})

    def insert_message(self, msg):
        self.messages.insert(END, f"{msg}")
        self.messages.yview(END)

    def insert_system_message(self, msg):
        self.messages.insert(END, msg)
        self.system_message_indexes.append(self.messages.size()-1)
        self.messages.itemconfig(self.messages.size()-1, {"fg": self.theme["fg_highlight"], "selectforeground": self.theme["fg_highlight"]})
    
    def insert_command_response(self, command, messages):
        start_index = self.messages.size()
        self.messages.insert(END, f"You used /{command}:")
        for msg in messages:
            self.messages.insert(END, f"|   {msg}")

        for i in range(start_index, self.messages.size()):
            self.system_message_indexes.append(i)
            self.messages.itemconfig(i, {"fg": self.theme["fg_highlight"], "selectforeground": self.theme["fg_highlight"]})
        
        self.messages.yview(END)

    def exit(self):
        msg = {
            "command": "exit"
        }

        send_command(self.s, msg)

        exit()
    
    def set_username(self, username):
        msg = {
            "command": "set_username",
            "username": username
        }

        send_command(self.s, msg)

        self.insert_command_response("username", [f"Set username to {username}"])

    def request_users(self):
        msg = {
            "command": "users"
        }

        send_command(self.s, msg)

    def send(self):
        msg = self.messagebox_var.get()
        if len(msg) < 1:
            return
        if msg[0] != "/":
            send_message(self.s, msg)
        else:
            if " " in msg:
                command, args = msg[1:].split(" ", 1)
            else:
                command = msg[1:]

            if command == "exit":
                self.exit()
            elif command == "username":
                self.set_username(args)
            elif command == "users":
                self.request_users()
            elif command == "theme":
                if args in THEMES:
                    self.theme = THEMES[args]
                    self.set_gui_theme()
                    self.insert_command_response("theme", [f"Set theme to {args}"])
                else:
                    self.insert_command_response("theme", [f"That is not a valid theme. Use /themes to see them"])
            elif command == "themes":
                msg = ["Themes: "]
                for i, theme in enumerate(THEMES):
                    if i == 0:
                        msg[0] += f"{theme}"
                    else:
                        msg[0] += f", {theme}"
                
                self.insert_command_response("themes", msg)
            else:
                self.insert_command_response(command, ["That is not a valid command."])

        self.messagebox_var.set("")


    def receive_loop(self):
        while True:
            msg = receive(self.s)
            if not msg:
                continue

            if msg["command"] == "message":
                self.insert_system_message(f"{msg['author']['username']}: {msg['message']}")
            
            elif msg["command"] == "user_join":
                self.insert_system_message(f"> {msg['user']} {choice(self.JOIN_MESSAGES)}")
            
            elif msg["command"] == "user_leave":
                self.insert_system_message(f"< {msg['user']} {choice(self.LEAVE_MESSAGES)}")
            
            elif msg["command"] == "users":
                self.insert_command_response("users", msg["users"])