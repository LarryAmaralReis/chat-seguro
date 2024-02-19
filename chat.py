import customtkinter as ctk
from CTkListbox import *
from CTkMessagebox import CTkMessagebox
from PIL import Image
from firebase import *

import socket
import threading
import json
from os import urandom
import binascii
from functions import *
import tkinter as tk

class Chat(tk.Tk):
    def __init__(self, login):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.resizable(False, False)
        self.nickname = get_nickname_by_login(login)
        self.title(f"CriptoChat - {self.nickname}")
        self.geometry("736x438")

        #------------------------------#
        self.server_socket = None
        self.udp_socket = None
        self.udp_port = self.get_free_port()

        self.udp_server_thread = threading.Thread(target=self.create_server_udp, args=(self.udp_port,))
        self.udp_server_thread.start()

        self.connect_server_tcp()
        self.online_users_dict = {
        }
        self.channels_dict = {
            20001: {
                'udp_address': ['127.0.0.1', 20001],
            },
            20002: {
                'udp_address': ['127.0.0.1', 20002],
            },
            20003: {
                'udp_address': ['127.0.0.1', 20003],
            }
        }
        self.channel_users = {}
        #------------------------------#
        self.current_conversation = None
        self.channel_conversation = None
        self.private_key = None
        self.public_key = None
        self.prime = None
        self.nonce = None
        #------------------------------#

        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, padx=10, pady=10)

        self.channels_list = CTkListbox(self.frame, width=100, height=350, command=self.confirm_join_channel)
        self.channels_list.grid(row=1, column=1, rowspan=2, padx=10)

        self.available_channels = [20001, 20002, 20003]
        for channel in self.available_channels:
            self.channels_list.insert(ctk.END, f"Canal {channel}")

        self.selected_channel = None

        self.conversation_area = ctk.CTkTextbox(self.frame, width=400, height=370, border_color="#4e4e4e", border_width=3)
        self.conversation_area.grid(row=1, column=2, rowspan=2, padx=10)
        self.conversation_area.configure(state="disabled")

        self.message_entry = ctk.CTkEntry(self.frame, width=200, placeholder_text="Mensagem")
        self.message_entry.grid(row=3, column=2, padx=10, pady=10)

        img = Image.open("enviar.png")
        self.message_button = ctk.CTkButton(self.frame, width=50, text="", corner_radius=32, fg_color="#0b6320", image=ctk.CTkImage(dark_image=img, light_image=img), command=self.send_message)
        self.message_button.place(x=470, y=380)

        x = Image.open("cancelar.png")
        self.close_button = ctk.CTkButton(self.frame, width=1, height=1, text="", corner_radius=32, fg_color="#1d1e1e", image=ctk.CTkImage(dark_image=x, light_image=x), command=self.close_conversation)
        self.close_button.configure(state="disabled")
        self.close_button.place(x=527, y=3)

        self.close_button_verify()

        self.online_users_list = CTkListbox(self.frame, width=100, height=350, command=self.solicitar)
        self.online_users_list.grid(row=1, column=3, rowspan=2, padx=10)

        self.running = True

        self.receive_thread = threading.Thread(target=self.receive_tcp_messages)
        self.receive_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.stop_threads)

    def connect_server_tcp(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect(("127.0.0.1", 20000))
            introduction_message = {
                'tipo': 1,
                'nickname': self.nickname,
                'udp_address': self.udp_socket.getsockname()
            }
            self.send_to_server(introduction_message, self.server_socket)
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
    
    def send_to_server(self, data_dict, socket):
        try:
            if socket and socket.fileno() != -1:
                json_data = json.dumps(data_dict)
                socket.sendall(json_data.encode("utf-8"))
        except Exception as e:
            print(f"Erro ao enviar dados privados: {e}")

    def receive_tcp_messages(self):
        while self.running:
            try:
                if self.server_socket:
                    data_server = self.server_socket.recv(1024).decode("utf-8")
                    if data_server:
                        self.handle_server_message(data_server)
            except Exception as e:
                print(f"Error receiving data from server: {e}")
                break

    def handle_server_message(self, data_server):
        try:
            received_data = json.loads(data_server)
            if received_data['tipo'] in [10, 2]:
                online_users = received_data['online_users']
                self.update_online_users(online_users)
        except json.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")

    def update_online_users(self, online_users):
        self.online_users_list.delete(0, ctk.END)
        #self.online_users_dict = {} 

        for username, address, udp_address in online_users:
            if username not in self.online_users_dict:
                # Adicione as informações do novo usuário ao dicionário
                self.online_users_dict[username] = {
                    'address': address,
                    'udp_address': udp_address,
                    'shared_key': None,
                    'nonce': None
                }
            if self.nickname != username:
                self.online_users_list.insert(ctk.END, username)
        print(self.online_users_dict)

    def get_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]
        
    def create_server_udp(self, porta):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("127.0.0.1", porta))

        receive_thread = threading.Thread(target=self.receive_udp_messages)
        receive_thread.start()

    def receive_udp_messages(self):
        while True:
            try:
                data, address = self.udp_socket.recvfrom(1024)
                print(f'Mensagem recebida de {address}: {data.decode("utf-8")}')

                data = json.loads(data)
                if data['tipo'] == 5:
                    self.solicitacao_recebida(data)
                if data['tipo'] == 6:
                    if self.online_users_dict[data['nickname']]['shared_key'] == None:
                        shared_key = key_exchange(self.private_key, data['public_key'], self.prime)
                        self.online_users_dict[data['nickname']]['shared_key'] = shared_key
                        self.online_users_dict[data['nickname']]['nonce'] = self.nonce

                    self.current_conversation = data['nickname']

                    self.conversation_area.configure(state="normal")
                    self.conversation_area.delete(1.0, ctk.END)
                    self.conversation_area.insert(ctk.END, f"[Servidor] Conversando com {self.current_conversation}!\n")
                    self.conversation_area.configure(state="disabled")

                    self.close_button_verify()

                    CTkMessagebox(title="Solicitação", message=f"Solicitação de {data['nickname']} aceita!", icon="check")
                if data['tipo'] == 7:
                    CTkMessagebox(title="Solicitação", message=f"Solicitação de {data['nickname']} negada!", icon="cancel")

                if data['tipo'] == 8:
                    CTkMessagebox(title="Alerta", message=f"{data['nickname']} fechou a conversa!", icon="warning")
                    self.current_conversation = None
                    self.close_button_verify()
                    self.conversation_area.configure(state="normal")
                    self.conversation_area.delete(1.0, ctk.END)
                    self.conversation_area.configure(state="disabled")
                if data['tipo'] == 10:
                    if data['nickname'] in self.online_users_dict:
                        print(f"Retirando {data['nickname']}")
                        del self.online_users_dict[data['nickname']]

                if data['tipo'] == 15:
                    address = tuple(self.online_users_dict[self.current_conversation]['udp_address'])
                    shared_key = self.online_users_dict[self.current_conversation]['shared_key']
                    nonce = self.online_users_dict[self.current_conversation]['nonce']

                    mensagem_criptografada = binascii.unhexlify(data['message'])
                    mensagem = decrypt_message(shared_key, mensagem_criptografada, nonce)

                    self.conversation_area.configure(state="normal")
                    self.conversation_area.insert(ctk.END, f"{data['nickname']}: {mensagem}\n")
                    self.conversation_area.configure(state="disabled")

                if data['tipo'] == 22:
                    self.channel_users = {}
                    self.channel_users = data['channel_users']

                    if self.online_users_dict[data['new_user']]['shared_key'] is None and data['new_user'] != self.nickname:
                        address = tuple(self.online_users_dict[data['new_user']]['udp_address'])
                        self.solicitar_dados(address)

                    if data['new_user'] != self.nickname:
                        self.conversation_area.configure(state="normal")
                        if self.channel_conversation is not None:
                            self.conversation_area.insert(ctk.END, f"[Canal {self.channel_conversation}]: {data['new_user']} entrou no canal!\n")
                        self.conversation_area.configure(state="disabled")
                    else:
                        self.conversation_area.configure(state="normal")
                        self.conversation_area.insert(ctk.END, f"[Canal {self.channel_conversation}] neste canal estão: {self.channel_users}\n")
                        self.conversation_area.configure(state="disabled")


                if data['tipo'] == 23:
                    self.responder_dados(data)

                if data['tipo'] == 24:
                    shared_key = key_exchange(self.private_key, data['public_key'], self.prime)
                    self.online_users_dict[data['nickname']]['shared_key'] = shared_key
                    self.online_users_dict[data['nickname']]['nonce'] = self.nonce
                    print(f"Chave compartilhada: {shared_key} - Prime: {self.prime}")
                
                if data['tipo'] == 25:
                    if self.channel_conversation is not None:
                        nickname = data['nickname']

                        shared_key = self.online_users_dict[nickname]['shared_key']
                        nonce = self.online_users_dict[nickname]['nonce']

                        mensagem_criptografada = binascii.unhexlify(data['message'])
                        mensagem = decrypt_message(shared_key, mensagem_criptografada, nonce)

                        self.conversation_area.configure(state="normal")
                        self.conversation_area.insert(ctk.END, f"{nickname}: {mensagem}\n")
                        self.conversation_area.configure(state="disabled")

                if data['tipo'] == 32:
                    self.channel_users = {}
                    self.channel_users = data['channel_users']

                    if data['old_user'] != self.nickname:
                        self.conversation_area.configure(state="normal")
                        if self.channel_conversation is not None:
                            self.conversation_area.insert(ctk.END, f"[Canal {self.channel_conversation}]: {data['old_user']} saiu do canal!\n")
                        self.conversation_area.configure(state="disabled")

            except Exception as e:
                print(f'Erro ao receber mensagem: {e}')

    def send_message(self):
        if self.current_conversation != None:
            self.conversation_area.configure(state="normal")
            self.conversation_area.insert(ctk.END, f"Você ({self.nickname}): {self.message_entry.get()}\n")
        
            message_text = self.message_entry.get()
            address = tuple(self.online_users_dict[self.current_conversation]['udp_address'])
            shared_key = self.online_users_dict[self.current_conversation]['shared_key']
            nonce = self.online_users_dict[self.current_conversation]['nonce']
            messagem_criptografada = encrypt_message(shared_key, message_text, nonce)
            message_text = binascii.hexlify(messagem_criptografada).decode('utf-8')

            message_data = {
                'tipo': 15,
                'nickname': self.nickname,
                'message': message_text
            }

            self.send_to_private(message_data, address)

            self.conversation_area.configure(state="disabled")
            self.message_entry.delete(0, ctk.END)

        if self.channel_conversation != None:
            self.conversation_area.configure(state="normal")
            self.conversation_area.insert(ctk.END, f"Você ({self.nickname}): {self.message_entry.get()}\n")

            aux = self.message_entry.get()

            for user in self.channel_users:
                if self.online_users_dict[user]['shared_key'] is not None and user != self.nickname:
                    message_text = aux
                    address = tuple(self.online_users_dict[user]['udp_address'])
                    shared_key = self.online_users_dict[user]['shared_key']
                    nonce = self.online_users_dict[user]['nonce']
                    messagem_criptografada = encrypt_message(shared_key, message_text, nonce)
                    message_text = binascii.hexlify(messagem_criptografada).decode('utf-8')

                    message_data = {
                        'tipo': 25,
                        'nickname': self.nickname,
                        'message': message_text
                    }

                    self.send_to_private(message_data, address)
                    self.message_entry.delete(0, ctk.END)

    def send_to_private(self, data_dict, address):
        try:
            if self.udp_socket and self.udp_socket.fileno() != -1:
                json_data = json.dumps(data_dict)
                self.udp_socket.sendto(json_data.encode("utf-8"),address)
        except Exception as e:
            print(f"Erro ao enviar dados privados: {e}")

    def solicitar(self, event=None):
        selected_user = self.online_users_list.get()
        if selected_user:
            msg = CTkMessagebox(title="Conversar com Usuário", message=f"Você deseja conversar com {selected_user}?", icon="question", option_1="Não", option_2="Sim")
            confirmation = msg.get()
            if confirmation == 'Sim':
                self.conversation_area.configure(state="normal")
                self.conversation_area.delete(1.0, ctk.END)
                self.conversation_area.configure(state="disabled")

                address = tuple(self.online_users_dict[selected_user]['udp_address'])

                #if self.online_users_dict[selected_user]['shared_key'] == None:
                self.private_key, public_key, self.prime = generate_dh_key_pair()
                self.nonce = urandom(16)
                aux = binascii.hexlify(self.nonce).decode('utf-8')
                #else:
                    #public_key = 3333333333
                    #self.prime = 3
                    #aux = "3"
                self.deactivate_listbox()
                self.enviar_solicitacao(address, public_key, self.prime, aux)

    def solicitar_dados(self, address):
        self.private_key, public_key, self.prime = generate_dh_key_pair()
        self.nonce = urandom(16)
        aux = binascii.hexlify(self.nonce).decode('utf-8')
        message = {
            'tipo': 23,
            'nickname': self.nickname,
            'public_key': public_key,
            'prime': self.prime,
            'nonce': aux
        }
        self.send_to_private(message, address)
    
    def responder_dados(self, data):
        nickname = data['nickname']
        address = tuple(self.online_users_dict[nickname]['udp_address'])
        public_key_recebida = data['public_key']
        prime = data['prime']
        nonce = binascii.unhexlify(data['nonce'])

        private_key, public_key, _ = generate_dh_key_pair(prime)
        shared_key = key_exchange(private_key, public_key_recebida, prime)
        self.online_users_dict[nickname]['shared_key'] = shared_key
        self.online_users_dict[nickname]['nonce'] = nonce
        print(f"Chave compartilhada: {shared_key} - Prime: {prime}")
        message = {
            'tipo': 24,
            'nickname': self.nickname,
            'public_key': public_key
        }

        self.send_to_private(message, address)

    def enviar_solicitacao(self, address, public_key, prime, nonce):
        self.close()
        self.close_channel()
        message = {
            'tipo': 5,
            'nickname': self.nickname,
            'public_key': public_key,
            'prime': prime,
            'nonce': nonce
        }
        self.send_to_private(message, address)

    def solicitacao_recebida(self, data):
        nickname = data['nickname']
        address = tuple(self.online_users_dict[nickname]['udp_address'])
        msg = CTkMessagebox(title="Conversar com Usuário", message=f"{nickname} deseja conversar com você, aceita?", icon="question", option_1="Não", option_2="Sim")
        confirmation = msg.get()
        if confirmation == 'Sim':
            self.close()
            self.close_channel()
            self.solicitacao_aceita(data, address)
        elif confirmation == 'Não':
            self.solicitacao_negada(address)
        
    def solicitacao_aceita(self, data, address):
        self.conversation_area.configure(state="normal")
        self.conversation_area.delete(1.0, ctk.END)
        self.conversation_area.configure(state="disabled")

        nickname = data['nickname']
        public_key = data['public_key']
        prime = data['prime']
        nonce = binascii.unhexlify(data['nonce'])

        self.conversation_area.configure(state="normal")
        self.conversation_area.insert(ctk.END, f"[Servidor] Conversando com {nickname}!\n")
        self.conversation_area.configure(state="disabled")

        if self.online_users_dict[nickname]['shared_key'] == None:
            self.private_key, self.public_key, _ = generate_dh_key_pair(prime)
            shared_key = key_exchange(self.private_key, public_key, prime)
            self.online_users_dict[nickname]['shared_key'] = shared_key
            self.online_users_dict[nickname]['nonce'] = nonce

        message = {
            'tipo': 6,
            'nickname': self.nickname,
            'public_key': self.public_key
        }
        self.send_to_private(message, address)
        
        self.current_conversation = nickname
        self.close_button_verify()
        self.deactivate_listbox()

    def solicitacao_negada(self, address):
        message = {
            'tipo': 7,
            'nickname': self.nickname,
        }
        self.send_to_private(message, address)

    def close_conversation(self):
        if self.current_conversation != None:
            msg = CTkMessagebox(title="Confirmação", message=f"Fechar conversa?", icon="warning", option_1="Não", option_2="Sim")
            confirmation = msg.get()
            if confirmation == 'Sim':
                address = tuple(self.online_users_dict[self.current_conversation]['udp_address'])
                message = {
                    'tipo': 8,
                    'nickname': self.nickname,
                }
                self.send_to_private(message, address)
                self.current_conversation = None
                self.close_button_verify()
                self.conversation_area.configure(state="normal")
                self.conversation_area.delete(1.0, ctk.END)
                self.conversation_area.configure(state="disabled")

            elif confirmation == 'Não':
                pass

        if self.channel_conversation != None:
            msg = CTkMessagebox(title="Confirmação", message=f"Fechar canal?", icon="warning", option_1="Não", option_2="Sim")
            confirmation = msg.get()
            if confirmation == 'Sim':
                self.deactivate_listbox()

                address = tuple(self.channels_dict[self.channel_conversation]['udp_address'])
                message = {
                    'tipo': 31,
                    'nickname': self.nickname,
                }
                self.send_to_private(message, address)
                self.channel_conversation = None
                self.close_button_verify()
                self.conversation_area.configure(state="normal")
                self.conversation_area.delete(1.0, ctk.END)
                self.conversation_area.configure(state="disabled")

            elif confirmation == 'Não':
                pass
        else:
            pass
    
    def close_button_verify(self):
        if self.current_conversation != None:
            self.close_button.configure(state="normal")
        elif self.channel_conversation != None:
            self.close_button.configure(state="normal")
        else:
            self.close_button.configure(state="disabled")

    def stop_threads(self):
        # Para as threads e fecha o socket
        self.close_conversation()
        self.running = False

        if self.server_socket:
            # Envia mensagem de desconexão ao fechar a janela
            disconnect_message = {
                'tipo': 10,
                'nickname': self.nickname,
                'udp_address': self.udp_socket.getsockname()
            }
            for username, user_info in self.online_users_dict.items():
                if user_info['shared_key'] is not None:
                    self.send_to_private(disconnect_message, tuple(user_info['udp_address']))
            self.send_to_server(disconnect_message, self.server_socket)
            self.server_socket.close()

        # Fecha o socket do servidor temporário
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except Exception as e:
                print(f"Erro ao fechar o socket udp: {e}")

        print("chegou aqui!")
        self.destroy()

    def close(self):
        if self.current_conversation != None:
            address = tuple(self.online_users_dict[self.current_conversation]['udp_address'])
            message = {
                'tipo': 8,
                'nickname': self.nickname,
            }
            self.send_to_private(message, address)
            self.current_conversation = None
            self.close_button_verify()
            self.conversation_area.configure(state="normal")
            self.conversation_area.delete(1.0, ctk.END)
            self.conversation_area.configure(state="disabled")
        else:
            pass

    def close_channel(self):
        if self.channel_conversation != None:
            address = tuple(self.channels_dict[self.channel_conversation]['udp_address'])
            message = {
                'tipo': 31,
                'nickname': self.nickname,
            }
            self.send_to_private(message, address)
            self.channel_conversation = None
            self.close_button_verify()
            self.conversation_area.configure(state="normal")
            self.conversation_area.delete(1.0, ctk.END)
            self.conversation_area.configure(state="disabled")
        else:
            pass

    def confirm_join_channel(self, event):
        selected_index = self.channels_list.curselection()
        if selected_index >= 0:
            selected_channel = self.available_channels[selected_index]
            msg = CTkMessagebox(title="Confirmação", message=f"Tem certeza de que deseja entrar no Canal {selected_channel}?", icon="question", option_1="Não", option_2="Sim")
            confirmation = msg.get()
            if confirmation == 'Sim':
                self.close()
                self.close_channel()
                self.connect_to_channel(selected_channel)
                print("Clicou sim para entrar no canal") 
            elif confirmation == 'Não':
                print("Clicou não para entrar no canal")
                self.channels_list.deactivate(selected_index)

    def connect_to_channel(self, selected_channel):
        self.channel_conversation = selected_channel
        self.close_button_verify()

        self.conversation_area.configure(state="normal")
        self.conversation_area.insert(ctk.END, f"[Canal {self.channel_conversation}] Seja bem-vindo(a)!\n")
        self.conversation_area.configure(state="disabled")

        address = tuple(self.channels_dict[selected_channel]['udp_address'])
        message = {
            'tipo': 21,
            'nickname': self.nickname,
            'udp_address': self.udp_socket.getsockname()
        }
        self.send_to_private(message, address)

    def deactivate_listbox(self):
        selected_indices = self.online_users_list.curselection()
        if selected_indices is not None:
            self.online_users_list.deactivate(selected_indices)

        selected_indices = self.channels_list.curselection()
        if selected_indices is not None:
            self.channels_list.deactivate(selected_indices)
