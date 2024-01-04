import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import json
from dh import *
from functions import *
from os import urandom
import binascii

class ChatApp:
    def __init__(self, root, nickname):
        self.root = root
        self.root.title(f"Chat App - {nickname}")
        self.client_socket = None
        self.nickname = nickname
        self.server_socket = None
        self.send_introduction_message()
        self.online_users_dict = {}
        self.temp_server_port = None
        self.temp_client_socket = None
        self.temp_server_socket = None

        self.nonce = None
        self.prime = None

        self.server_public_key = None
        self.server_private_key = None
        self.server_shared_key = None
        self.client_public_key = None
        self.client_public_key = None
        self.client_shared_key = None

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

        # Vincula a função de exibir menu de contexto à lista de usuários online
        self.online_users_list.bind("<Double-1>", self.send_message_to_user)

        # Menu de contexto para usuários online
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Enviar Mensagem", command=self.send_message_to_user)

        # Botão de desconexão
        disconnect_button = tk.Button(root, text="Desconectar", command=self.disconnect_private)
        disconnect_button.grid(row=2, column=3, padx=5, pady=5)


        # Flag para indicar se a thread deve continuar executando
        self.running = True

        # Inicia a thread para receber mensagens do servidor
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()

        # Vincula a função de encerramento da janela à função stop_threads
        self.root.protocol("WM_DELETE_WINDOW", self.stop_threads)

    def stop_threads(self):
        # Para as threads e fecha o socket
        self.running = False
        if self.server_socket:
            # Envia mensagem de desconexão ao fechar a janela
            disconnect_message = {
                'tipo': 10,
                'nickname': self.nickname
            }
            self.send_to_private(disconnect_message, self.server_socket)
            self.server_socket.close()
        if self.client_socket:
            try:
                # Envia mensagem de desconexão
                self.send_disconnect_message()
                self.client_socket.close()
            except Exception as e:
                print(f"Erro ao fechar o socket: {e}")

        # Fecha o socket do servidor temporário
        if self.temp_server_port:
            try:
                temp_server_address = ("127.0.0.1", self.temp_server_port)
                temp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_client_socket.connect(temp_server_address)
                temp_client_socket.close()
            except Exception as e:
                print(f"Erro ao fechar o socket do servidor temporário: {e}")

        # Fecha o socket do cliente temporário
        if self.temp_client_socket:
            try:
                self.temp_client_socket.close()
            except Exception as e:
                print(f"Erro ao fechar o socket do cliente temporário: {e}")

        self.root.destroy()

    def confirm_join_channel(self, event):
        self.disconnect_private()

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
            self.receive_thread = threading.Thread(target=self.receive_messages_channel)
            self.receive_thread.start()
        except Exception as e:
            print(f"Erro ao conectar ao servidor do canal: {e}")

    def update_conversation_area(self):
        if self.selected_channel:
            self.conversation_area.delete(1.0, tk.END)
            self.conversation_area.insert(tk.END, f"|------------ Canal  {self.selected_channel} ------------|\n")

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def send_message_to_user(self, event=None):
        selected_user = self.online_users_list.get(tk.ACTIVE)
        if selected_user:
            confirmation = messagebox.askquestion("Conectar-se ao Usuário",
                                                f"Você deseja se conectar a {selected_user}?")
            if confirmation == 'yes':
                self.disconnect_private()
                self.connect_to_user(selected_user)
                # Limpa a área de conversa para uma nova conversa privada
                self.conversation_area.delete(1.0, tk.END)

    def connect_to_user(self, other_user):
        # Função para se conectar a outro usuário
        connect_message = {
            'tipo': 7,  # Tipo 7 indica mensagem de solicitação de conexão a outro usuário
            'from_user': self.nickname,
            'to_user': other_user
        }
        self.send_to_private(connect_message, self.server_socket)

    def send_message(self):
        message_text = self.message_entry.get()
        if message_text:
            if self.selected_channel or self.temp_client_socket or self.temp_server_socket:
                if self.temp_client_socket:
                    # Envia mensagem para o outro cliente privado
                    mensagem_area = message_text
                    messagem_criptografada = encrypt_message(self.client_shared_key, message_text, self.nonce)
                    message_text = binascii.hexlify(messagem_criptografada).decode('utf-8')
                    message_data = {
                        'tipo': 15,
                        'nickname': self.nickname,
                        'message': message_text
                    }
                    self.send_to_private(message_data, self.temp_client_socket)
                    self.conversation_area.insert(tk.END, f"Você ({message_data['nickname']}): {mensagem_area}\n")
                    self.message_entry.delete(0, tk.END)
                elif self.temp_server_socket:
                    # Envia mensagem para o outro cliente privado
                    mensagem_area = message_text
                    messagem_criptografada = encrypt_message(self.server_shared_key, message_text, self.nonce)
                    message_text = binascii.hexlify(messagem_criptografada).decode('utf-8')
                    message_data = {
                        'tipo': 15,
                        'nickname': self.nickname,
                        'message': message_text
                    }
                    self.send_to_private(message_data, self.temp_server_socket)
                    self.conversation_area.insert(tk.END, f"Você ({message_data['nickname']}): {mensagem_area}\n")
                    print(f"Servidor {self.nickname} está enviando mensagem para {self.temp_server_socket.getpeername()[1]}")
                    self.message_entry.delete(0, tk.END)
                else:
                    # Se não houver cliente temporário, envia para o canal
                    nickname = self.nickname
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
            if self.client_socket and self.client_socket.fileno() != -1:  # Verifica se o socket está aberto
                json_data = json.dumps(data_dict)
                self.client_socket.sendall(json_data.encode("utf-8"))
        except Exception as e:
            print(f"Erro ao enviar dados para o servidor: {e}")

    def receive_messages(self):
        # Function to receive messages from both the server and the channel
        while self.running:
            try:
                if self.server_socket:
                    data_server = self.server_socket.recv(1024).decode("utf-8")
                    if data_server:
                        self.handle_server_message(data_server)

            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    def handle_server_message(self, data_server):
        try:
            received_data = json.loads(data_server)
            # Process messages from the server
            if received_data['tipo'] in [10, 2]:
                # Message type 10 or 2 indicates an update to the online users list
                online_users = received_data['online_users']
                self.update_online_users(online_users)
            elif received_data['tipo'] == 7:
                # Connection request message
                self.handle_connection_request(received_data['from_user'])
            elif received_data['tipo'] == 8:
                # Connection acceptance message
                self.handle_connection_acceptance(received_data)
            elif received_data['tipo'] == 9:
                # Connection decline message
                self.handle_connection_decline(received_data['from_user'])
        except json.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")

    def receive_messages_channel(self):
        # Function to receive messages from both the server and the channel
        while self.running:
            try:
                if self.client_socket:
                    data_channel = self.client_socket.recv(1024).decode("utf-8")
                    if data_channel:
                        self.handle_channel_message(data_channel)

            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    def handle_channel_message(self, data_channel):
        try:
            received_data = json.loads(data_channel)
            if received_data['tipo'] == 0:
                pass
            else:
                # Other message types
                self.conversation_area.insert(tk.END, f"{received_data['nickname']} ({received_data['channel']}): {received_data['message']}\n")

        except json.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")

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
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect(("127.0.0.1", 20000))

            # Enviar mensagem de apresentação
            introduction_message = {
                'tipo': 1,  # Tipo 1 indica uma mensagem de apresentação
                'nickname': self.nickname
            }
            self.send_to_private(introduction_message, self.server_socket)
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
            
    def update_online_users(self, online_users):
        # Função para atualizar a lista de usuários online na interface gráfica
        self.online_users_list.delete(0, tk.END)  # Limpa a lista atual
        self.online_users_dict = {} 

        for username, address in online_users:
            self.online_users_dict[username] = {'address': address}
            self.add_online_user(username)

    def add_online_user(self, username):
        if self.nickname != username:
            self.online_users_list.insert(tk.END, username)

    def handle_connection_request(self, from_user):
        # Função para lidar com o pedido de conexão de outro usuário
        confirmação = messagebox.askquestion("Pedido de Conexão", f"{from_user} quer se conectar. Aceitar o pedido?")
        if confirmação == 'yes':
            # Cria um servidor temporário para a conexão
            self.temp_server_port = self.get_free_port()
            temp_server_thread = threading.Thread(target=self.create_server, args=(self.temp_server_port,))
            temp_server_thread.start()

            # Envia uma mensagem ao servidor sobre a aceitação do pedido e a porta do servidor temporário
            mensagem_aceitacao = {
                'tipo': 8,
                'from_user': self.nickname,
                'to_user': from_user,
                'temp_server_port': self.temp_server_port
            }
            self.send_to_private(mensagem_aceitacao, self.server_socket)
            self.conversation_area.delete(1.0, tk.END)
            self.conversation_area.insert(tk.END, f"|------ Conversando com {mensagem_aceitacao['to_user']} -----|\n")
        else:
            # Envia uma mensagem ao servidor sobre a recusa do pedido
            mensagem_recusa = {
                'tipo': 9,
                'from_user': self.nickname,
                'to_user': from_user,
            }
            self.send_to_private(mensagem_recusa, self.server_socket)

    def handle_connection_acceptance(self, dados_recebidos):
        # Lidar com a aceitação de um pedido de conexão
        messagebox.showinfo("Pedido Aceito", f"{dados_recebidos['from_user']} aceitou seu pedido de conexão. A comunicação será estabelecida.")

        # Conectar ao servidor temporário do outro usuário
        temp_server_address = ("127.0.0.1", dados_recebidos['temp_server_port'])
        self.temp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.temp_client_socket.connect(temp_server_address)

        # Inicia uma thread para receber mensagens do servidor temporário
        temp_receive_thread = threading.Thread(target=self.receive_temp_messages)
        temp_receive_thread.start()

        # Lógica adicional se necessário
        self.conversation_area.insert(tk.END, f"|------ Conversando com {dados_recebidos['from_user']} -----|\n")


    def handle_connection_decline(self, from_user):
        # Função para lidar com a recusa de solicitação de conexão do tipo 9
        messagebox.showinfo("Solicitação Recusada", f"{from_user} recusou sua solicitação de conexão.")
        # Aqui você pode adicionar a lógica adicional se necessário.

    def get_free_port(self):
        # Encontra uma porta livre para o servidor temporário
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]
        
    def create_server(self, porta):
        # Cria um servidor para lidar com conexões de outros clientes
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("127.0.0.1", porta))
        server_socket.listen(5)

        print(f"Servidor temporário escutando em {porta}")

        server_private_key, server_public_key, prime = generate_dh_key_pair()
        nonce = urandom(16)
        aux = nonce
        self.server_private_key = server_private_key
        self.server_public_key = server_public_key
        self.prime = prime
        self.nonce = binascii.hexlify(nonce).decode('utf-8')

        dados = {
                'tipo': 100,
                'nickname': self.nickname,
                'prime': self.prime,
                'server_public_key': self.server_public_key,
                'nonce': self.nonce
            }
        
        while True:
            client_socket, address = server_socket.accept()
            print(f"Conexão aceita de {address} na porta {porta}")
            self.temp_server_socket = client_socket
            # Inicia uma thread para lidar com a comunicação com o cliente
            thread_cliente_handler = threading.Thread(target=self.handle_client_temp, args=(client_socket, address, porta))
            thread_cliente_handler.start()

            self.send_to_private(dados, self.temp_server_socket)
            self.nonce = aux
            

    def receive_temp_messages(self):
        # Recebe mensagens do servidor temporário
        while self.running:
            try:
                data = self.temp_client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                print(f"Mensagem recebida do servidor temporário: {data}")

                message_data = json.loads(data)
                if message_data['tipo'] == 100:
                    self.prime = message_data['prime']
                    self.server_public_key = message_data['server_public_key']
                    self.nonce = binascii.unhexlify(message_data['nonce'])

                    client_private_key, client_public_key, _ = generate_dh_key_pair(self.prime)

                    self.client_private_key = client_private_key
                    self.client_public_key = client_public_key

                    dados = {
                        'tipo': 100,
                        'nickname': self.nickname,
                        'client_public_key': self.client_public_key,
                    }

                    self.send_to_private(dados, self.temp_client_socket)

                    self.client_shared_key = key_exchange(self.client_private_key, self.server_public_key, self.prime)
                    print(f"Chave compartilhada do client:{self.client_shared_key}")

                elif message_data['tipo'] == 15:
                    mensagem_criptografada = binascii.unhexlify(message_data['message'])
                    mensagem = decrypt_message(self.client_shared_key, mensagem_criptografada, self.nonce)
                    self.conversation_area.insert(tk.END, f"{message_data['nickname']}: {mensagem}\n")
                elif message_data['tipo'] == 20:
                    self.disconnect_private()

            except Exception as e:
                print(f"Erro ao receber dados do servidor temporário: {e}")
                break

    def handle_client_temp(self, client_socket, address, porta_canal):
        # Lida com a comunicação com um cliente conectado ao servidor temporário
        try:
            # Lógica adicional para lidar com mensagens do cliente
            while True:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                print(f"Mensagem recebida do cliente {address} na porta {porta_canal}: {data}")
                
                message_data = json.loads(data)
                if message_data['tipo'] == 100:
                    self.client_public_key = message_data['client_public_key']
                    self.server_shared_key = key_exchange(self.server_private_key, self.client_public_key, self.prime)
                    print(f"Chave compartilhada do servidor:{self.server_shared_key}")
                    
                elif message_data['tipo'] == 15:
                    mensagem_criptografada = binascii.unhexlify(message_data['message'])
                    mensagem = decrypt_message(self.server_shared_key, mensagem_criptografada, self.nonce)
                    self.conversation_area.insert(tk.END, f"{message_data['nickname']}: {mensagem}\n")
                elif message_data['tipo'] == 20:
                    self.disconnect_private()

        except Exception as e:
            print(f"Erro ao lidar com o cliente {address} na porta {porta_canal}: {e}")
        finally:
            client_socket.close()
    
    def send_to_private(self, data_dict, socket):
        # Função para enviar dados diretamente
        try:
            if socket and socket.fileno() != -1:
                json_data = json.dumps(data_dict)
                socket.sendall(json_data.encode("utf-8"))
        except Exception as e:
            print(f"Erro ao enviar dados privados: {e}")

    def disconnect_private(self):
        dados = {
            'tipo': 20
        }
        if self.temp_server_socket:
            try:
                self.send_to_private(dados, self.temp_server_socket)
                self.temp_server_socket.close()
            except Exception as e:
                print(f"Erro ao fechar o socket do servidor temporário: {e}")

        if self.temp_client_socket:
            try:
                self.send_to_private(dados, self.temp_client_socket)
                self.temp_client_socket.close()
            except Exception as e:
                print(f"Erro ao fechar o socket do cliente temporário: {e}")

        # Limpar outras variáveis relacionadas à conexão privada
        self.temp_client_socket = None
        self.temp_server_socket = None

        self.nonce = None
        self.prime = None

        self.server_public_key = None
        self.server_private_key = None
        self.server_shared_key = None
        self.client_public_key = None
        self.client_public_key = None
        self.client_shared_key = None

        self.conversation_area.delete(1.0, tk.END)



