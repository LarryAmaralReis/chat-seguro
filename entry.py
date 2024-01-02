import tkinter as tk
from chat import *

class NicknameEntry:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback

        self.root.title("Chat Criptografado")
        self.root.geometry("300x150")

        self.label = tk.Label(root, text="Digite seu Nome:")
        self.label.pack(pady=10)

        self.nickname_entry = tk.Entry(root, width=30)
        self.nickname_entry.pack(pady=10)

        self.enter_button = tk.Button(root, text="Entrar", command=self.enter_chat)
        self.enter_button.pack(pady=10)

    def enter_chat(self):
        nickname = self.nickname_entry.get()
        if nickname:
            self.root.destroy()  # Destroi a janela de entrada de nickname
            chat_root = tk.Tk()
            chat_app = ChatApp(chat_root, nickname)
            chat_root.mainloop()