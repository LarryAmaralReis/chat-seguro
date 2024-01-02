import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import json

class ChatApp:
    def __init__(self, root, nickname):
        self.root = root
        self.root.title("Chat App")
        self.client_socket = None
        self.nickname = nickname
        self.send_introduction_message()

        # Lista de canais disponíveis
        self.channels_list = tk.Listbox(root, selectmode=tk.SINGLE, height=20)
        self.channels_list.grid(row=0, column=0, padx=10, pady=10)

        # Adiciona os canais disponíveis à lista
        self.available_channels = [20001, 20002, 20003]
        for channel in self.available_channels:
            self.channels_list.insert(tk.END, f"Canal {channel}")

        # Canal selecionado
        self.selected_channel = None

        # Vincula a função de atualização da área de conversa à seleção de um canal
        self.channels_list.bind("<Double-1>", self.confirm_join_channel)

        # Área para mostrar as mensagens
        self.conversation_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=20)
        self.conversation_area.grid(row=0, column=1, rowspan=2, padx=10, pady=10)

        # Área para enviar mensagens
        self.message_entry = tk.Entry(root, width=30)
        self.message_entry.grid(row=2, column=1, padx=10, pady=5)

        # Botão para enviar mensagem
        send_button = tk.Button(root, text="Enviar", command=self.send_message)
        send_button.grid(row=2, column=2, padx=5, pady=5)

        # Vincula a função de exibir menu de contexto à lista de usuários online
        self.online_users_list = tk.Listbox(root, width=15, height=20)
        self.online_users_list.grid(row=0, column=3, rowspan=2, padx=10, pady=10)

        # Menu de contexto para usuários online
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Enviar Mensagem", command=self.send_message_to_user)

        # Flag para indicar se a thread deve continuar executando
        self.running = True

        # Inicia a thread para receber mensagens do servidor
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()

        # Vincula a função de encerramento da janela à função stop_threads
        self.root.protocol("WM_DELETE_WINDOW", self.stop_threads)

    def stop_threads(self):
        # Função para encerrar a execução das threads antes de fechar a janela
        self.running = False
        if self.client_socket:
            # Envia mensagem de desconexão ao fechar a janela
            disconnect_message = {
                'tipo': 10,
                'nickname': self.nickname
            }
            self.send_to_server(disconnect_message)
            self.client_socket.close()
        self.root.destroy()

    def confirm_join_channel(self, event):
        selected_index = self.channels_list.curselection()
        if selected_index:
            self.send_disconnect_message()

            selected_channel = self.available_channels[selected_index[0]]
            confirmation = messagebox.askquestion("Confirmação",
                                                f"Tem certeza de que deseja entrar no Canal {selected_channel}?")
            if confirmation == 'yes':
                self.selected_channel = selected_channel
                self.connect_to_server()
                messagebox.showinfo("Canal Selecionado", f"Entrou no Canal {self.selected_channel}")
                self.send_connect_message()
                self.update_conversation_area()

    def connect_to_server(self):
        # Função para conectar ao servidor do canal
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", self.selected_channel))
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
        except Exception as e:
            print(f"Erro ao conectar ao servidor do canal: {e}")

    def update_conversation_area(self):
        if self.selected_channel:
            self.conversation_area.delete(1.0, tk.END)
            self.conversation_area.insert(tk.END, f"|------------ Canal  {self.selected_channel} ------------|\n")

    def add_online_user(self, username):
        self.online_users_list.insert(tk.END, username)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def send_message_to_user(self):
        selected_user = self.online_users_list.get(tk.ACTIVE)
        if selected_user:
            messagebox.showinfo("Enviar Mensagem", f"Enviar mensagem para {selected_user}")

    def send_message(self):
        message_text = self.message_entry.get()
        if message_text:
            if self.selected_channel:
                # Obtendo o nickname do próprio objeto ChatApp
                nickname = self.nickname
                # Criando um dicionário aninhado para a mensagem
                message_data = {
                    'tipo': 5,
                    'channel': self.selected_channel,
                    'nickname': nickname,
                    'message': message_text
                }
                self.send_to_server(message_data)
            self.conversation_area.insert(tk.END, f"Você ({message_data['nickname']}): {message_data['message']}\n")
            self.message_entry.delete(0, tk.END)

    def send_to_server(self, data_dict):
        # Função para enviar dados (dicionário) para o servidor
        try:
            if self.client_socket:
                json_data = json.dumps(data_dict)
                self.client_socket.sendall(json_data.encode("utf-8"))
        except Exception as e:
            print(f"Erro ao enviar dados para o servidor: {e}")

    def receive_messages(self):
        # Função para receber mensagens do servidor
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode("utf-8")
                if data:
                    print(f"Mensagem recebida do servidor: {data}")
                    try:
                        received_data = json.loads(data)

                        # Verifica o tipo da mensagem
                        if received_data['tipo'] == 10 or 2:
                            # Mensagem de atualização da lista de usuários online
                            online_users = received_data['online_users']
                            self.update_online_users(online_users)
                        else:
                            # Outros tipos de mensagens
                            self.conversation_area.insert(tk.END, f"{received_data['nickname']} ({received_data['channel']}): {received_data['message']}\n")

                    except json.JSONDecodeError as json_error:
                        print(f"Erro ao decodificar JSON: {json_error}")
            except Exception as e:
                print(f"Erro ao receber dados do servidor: {e}")
                break

    def send_connect_message(self):
        if self.selected_channel:
            # Criando um dicionário aninhado para a mensagem de desconexão
            connect_message = {
                'tipo': 5,
                'channel': self.selected_channel,
                'nickname': self.nickname,
                'message': f"{self.nickname} entrou no canal."
            }
            self.send_to_server(connect_message)

    def send_disconnect_message(self):
        if self.selected_channel:
            # Criando um dicionário aninhado para a mensagem de desconexão
            disconnect_message = {
                'tipo': 6,
                'channel': self.selected_channel,
                'nickname': self.nickname,
                'message': f"{self.nickname} saiu do canal."
            }
            self.send_to_server(disconnect_message)

    def send_introduction_message(self):
        # Função para enviar a mensagem de apresentação assim que o cliente entrar no ChatApp
        try:
            # Conectar ao servidor na porta 20000
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", 20000))

            # Enviar mensagem de apresentação
            introduction_message = {
                'tipo': 1,  # Tipo 1 indica uma mensagem de apresentação
                'nickname': self.nickname
            }
            self.send_to_server(introduction_message)
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
            
    def update_online_users(self, online_users):
        # Função para atualizar a lista de usuários online na interface gráfica
        self.online_users_list.delete(0, tk.END)  # Limpa a lista atual

        for username in online_users:
            self.add_online_user(username)
