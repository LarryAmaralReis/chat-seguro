import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from firebase import *
from chat import *


class Entry(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CriptoChat")
        self.geometry("500x300")
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, padx=10, pady=10)

        self.label = ctk.CTkLabel(self.frame, text="Fazer Login", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(padx=10, pady=10)

        self.email = ctk.CTkEntry(self.frame, placeholder_text="E-mail")
        self.email.grid(padx=10, pady=10)

        self.senha = ctk.CTkEntry(self.frame, placeholder_text="Senha")
        self.senha.grid(padx=10, pady=10)

        self.botao1 = ctk.CTkButton(self.frame, text="Logar", command=self.login)
        self.botao1.grid(padx=10, pady=10)

        self.botao2 = ctk.CTkButton(self, text="Não possui conta?",text_color="#000000", fg_color="#fcba03", command=self.load_register)
        self.botao2.grid(row=1, column=0, padx=10, pady=10)

    
    def is_nickname_duplicate(nickname_to_check):
        all_users = db.child("users").get()
        for user in all_users.each():
            user_data = user.val()
            if 'nickname' in user_data and user_data['nickname'] == nickname_to_check:
                return True
        return False

    def login(self):
        email = self.email.get()
        senha = self.senha.get()
        try:
            login = auth.sign_in_with_email_and_password(email, senha)
            CTkMessagebox(title="CriptoChat", icon="check", message="Login realizado com sucesso!")
            self.login_complete(login)
        except Exception as e:
            CTkMessagebox(title="CriptoChat", icon="cancel", message="Erro ao tentar fazer login.")
            print(e)

    def register(self):
        email = self.email.get()
        senha = self.senha.get()
        nickname = self.nickname_entry.get()
        try:
            if is_nickname_duplicate(nickname):
                raise NicknameDuplicadoException("Nickname já está em uso.")

            user = auth.create_user_with_email_and_password(email, senha)
            user_data = {
                'nickname': nickname,
                'email': email
            }
            results = db.child("users").child(user['localId']).set(user_data)
            CTkMessagebox(title="CriptoChat", icon="check", message="Registro realizado com sucesso!")
            self.load_login()
        except NicknameDuplicadoException:
            CTkMessagebox(title="CriptoChat", icon="warning", message="Nickname já está em uso.")
        except Exception as e:
            CTkMessagebox(title="CriptoChat", icon="cancel", message="Erro ao tentar fazer registro.")

    def load_register(self):
        self.label.configure(text="Fazer Registro")
        self.botao1.configure(text="Registrar", command=self.register)
        self.botao1.grid(row=4, column=0, padx=10, pady=10)
        self.botao2.configure(text="Já possui conta?", command=self.load_login)
        self.nickname_entry = ctk.CTkEntry(self.frame, placeholder_text="Nickname")
        self.nickname_entry.grid(row=3, column=0, padx=10, pady=10)

    def load_login(self):
        self.label.configure(text="Fazer Login")
        self.botao1.configure(text="Logar", command=self.login)
        self.botao2.configure(text="Não possui conta?", command=self.load_register)
        self.nickname_entry.grid_forget()

    def login_complete(self, login):
        self.withdraw()
        self.quit()
        chat_app = Chat(login)
        chat_app.mainloop()

