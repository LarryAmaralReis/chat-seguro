import tkinter as tk
from tkinter import messagebox
from firebase import *
from chat import *
from auth import *


class Entry(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("CriptoChat")
        self.geometry("500x300")
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=0, padx=10, pady=10)

        self.label = tk.Label(self.frame, text="Fazer Login", font=("Arial", 20, "bold"))
        self.label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.label_email = tk.Label(self.frame, text="E-mail")
        self.label_email.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.email_entry = tk.Entry(self.frame)
        self.email_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.label_senha = tk.Label(self.frame, text="Senha")
        self.label_senha.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.senha_entry = tk.Entry(self.frame, show="*")
        self.senha_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.botao1 = tk.Button(self.frame, text="Logar", command=self.login)
        self.botao1.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.botao2 = tk.Button(self, text="Não possui conta?", command=self.load_register)
        self.botao2.grid(row=1, column=0, padx=10, pady=10)

    
    def is_nickname_duplicate(nickname_to_check):
        all_users = db.child("users").get()
        for user in all_users.each():
            user_data = user.val()
            if 'nickname' in user_data and user_data['nickname'] == nickname_to_check:
                return True
        return False

    def login(self):
        self.botao1.configure(state="disabled")
        email = self.email_entry.get()
        senha = self.senha_entry.get()
        try:
            self.login_user = auth.sign_in_with_email_and_password(email, senha)
            self.authentication(email)
        except Exception as e:
            messagebox.showinfo("CriptoChat", "Erro ao tentar fazer login!")
            self.botao1.configure(state="normal")
            print(e)

    def register(self):
        self.botao1.configure(state="disabled")
        self.email = self.email_entry.get()
        self.senha = self.senha_entry.get()
        self.nickname = self.nickname_entry.get()
        try:
            if is_nickname_duplicate(self.nickname):
                raise NicknameDuplicadoException("Nickname já está em uso.")
            
            self.auth_register(self.email)

        except NicknameDuplicadoException:
            messagebox.showinfo("CriptoChat", "Nickname já está em uso!")
        except Exception as e:
            messagebox.showinfo("CriptoChat", "Erro ao tentar fazer registro!")
            self.botao1.configure(state="normal")

    def load_register(self):
        self.label.configure(text="Fazer Registro")
        self.botao1.configure(text="Registrar", command=self.register)
        self.botao1.grid(row=4, column=0, padx=10, pady=10)
        self.botao2.configure(text="Já possui conta?", command=self.load_login)
        self.nickname_entry = tk.Entry(self.frame, textvariable="Nickname")
        self.nickname_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        self.label_nickname = tk.Label(self.frame, text="Nickname")
        self.label_nickname.grid(row=3, column=0, padx=10, pady=5, sticky="w")

    def load_login(self):
        self.label.configure(text="Fazer Login")
        self.botao1.configure(text="Logar", command=self.login, state="normal")
        self.botao2.configure(text="Não possui conta?", command=self.load_register)
        self.nickname_entry.grid_forget()
        self.label_nickname.grid_forget()

    def authentication(self, email):
        self.cod = enviar_email(email)
        self.janela = tk.Toplevel()
        self.janela.title("Autenticação")
        self.janela.geometry("325x130")
        self.label_janela = tk.Label(self.janela, text="Insira o código recebido no e-mail",font=("Arial", 15, "bold"))
        self.label_janela.grid(row=0, column=0, pady=10)
        self.codigo_janela = tk.Entry(self.janela, show="*")
        self.codigo_janela.grid(row=1, column=0, pady=10)
        self.botao_janela = tk.Button(self.janela, text="Verificar", command=self.verify_code)
        self.botao_janela.grid(row=2, column=0, pady=10)
        self.janela.lift()

    def verify_code(self):
        codigo = self.codigo_janela.get()

        if codigo == str(self.cod):
            messagebox.showinfo("Autenticação", "Login realizado com sucesso!")
            self.janela.destroy()
            self.login_complete(self.login_user)
        else:
            messagebox.showerror("Autenticação", "Autenticação falhou!")
            self.botao1.configure(state="normal")
            self.janela.destroy()

    def login_complete(self, login):
        self.destroy()
        chat_app = Chat(login)
        chat_app.mainloop()

    def auth_register(self, email):
        self.cod = enviar_email(email)
        self.janela = tk.Toplevel()
        self.janela.title("Autenticação")
        self.janela.geometry("325x130")
        self.label_janela = tk.Label(self.janela, text="Insira o código recebido no e-mail",font=("Arial", 15, "bold"))
        self.label_janela.grid(row=0, column=0, pady=10)
        self.codigo_janela = tk.Entry(self.janela, show="*")
        self.codigo_janela.grid(row=1, column=0, pady=10)
        self.botao_janela = tk.Button(self.janela, text="Verificar", command=self.verify_code_register)
        self.botao_janela.grid(row=2, column=0, pady=10)
        self.janela.lift()

    def verify_code_register(self):
        codigo = self.codigo_janela.get()

        if codigo == str(self.cod):
            messagebox.showinfo("Autenticação", "Autenticação realizada com sucesso!")
            self.janela.destroy()
            self.register_complete()
        else:
            messagebox.showerror("Autenticação", "Autenticação falhou!")
            self.botao1.configure(state="normal")
            self.janela.destroy()
            raise Exception("Falha na autenticação!")
        
    def register_complete(self):
            user = auth.create_user_with_email_and_password(self.email, self.senha)
            user_data = {
                'nickname': self.nickname,
                'email': self.email
            }
            results = db.child("users").child(user['localId']).set(user_data)
            messagebox.showinfo("CriptoChat", "Registro realizado com sucesso!")
            self.load_login()

