import socket
import threading
import json
import binascii
from functions import *

class ChatServer:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 20000
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = set()
        self.online_users = set()
        self.nickname_to_socket = {}
        self.lock = threading.Lock()
        self.active_threads = set()

        #------------------------------#
        self.master_key = 54454969524667022591300178147674637787134628051833060362233619131391366951278
        self.master_nonce = b'Z\x06\x98p#Z\xab\xc3\x81\x91\xf0\xec1\xb8\x03?'
        #------------------------------#

        print(f"Servidor escutando em {self.host}:{self.port}")

        # Thread para aceitar novas conexões
        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.start()

    def accept_connections(self):
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"Conexão aceita de {address}")

                # Adiciona o novo cliente à lista de clientes
                with self.lock:
                    self.clients.add(client_socket)

                # Thread para lidar com o cliente
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                self.active_threads.add(client_handler)
                client_handler.start()

        except Exception as e:
            print(f"Erro ao aceitar conexões: {e}")
        finally:
            self.server_socket.close()


    def stop_server(self):
        # Função para parar o servidor e aguardar o término de todas as threads
        for thread in self.active_threads:
            thread.join()

        print("Servidor encerrado.")

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break

                mensagem_criptografada = binascii.unhexlify(data)
                mensagem = decrypt_message(self.master_key, mensagem_criptografada, self.master_nonce)
                data = json.loads(mensagem)
                tag = binascii.unhexlify(data['tag'])
                received_data = json.loads(data['message'])
                received_data_tag = json.dumps(received_data)

                verify_tag(self.master_key, received_data_tag, tag)

                print(f"Mensagem recebida do cliente {client_socket.getpeername()}: {data['message']}")

                message_data = received_data

                if message_data['tipo'] == 1:  # Tipo 1 indica mensagem de entrada
                    with self.lock:
                        user_info = (
                            message_data['nickname'],
                            client_socket.getpeername(),  # Obtém o endereço IP do cliente conectado
                            tuple(message_data['udp_address'])
                        )
                        self.online_users.add(user_info)
                        # Adiciona ao dicionário de nickname para socket
                        self.nickname_to_socket[message_data['nickname']] = client_socket

                    # Envia a lista de usuários online para todos os clientes
                    online_users_message = json.dumps({
                        'tipo': 2,  # Tipo 2 indica mensagem de lista de usuários online
                        'online_users': list(self.online_users)
                    })
                    print(f"DIC ONLINE USERS: {online_users_message}")
                    self.broadcast_message(online_users_message)

                elif message_data['tipo'] == 10:
                    with self.lock:
                        user_info = (
                            message_data['nickname'],
                            client_socket.getpeername(),
                            tuple(message_data['udp_address'])
                        )
                        if user_info in self.online_users:
                            self.online_users.remove(user_info)

                        # Remove do dicionário de nickname para socket
                        del self.nickname_to_socket[message_data['nickname']]

                    # Envia a lista de usuários online para todos os clientes
                    online_users_message = json.dumps({
                        'tipo': 10,  # Tipo 10 indica mensagem de lista de usuários online
                        'online_users': list(self.online_users)
                    })
                    print(f"DIC ONLINE USERS: {online_users_message}")
                    self.broadcast_message(online_users_message)
                
                elif message_data['tipo'] == 7:  # Tipo 7 indica solicitação de conexão a outro usuário
                    with self.lock:
                        from_user = message_data['from_user']
                        to_user = message_data['to_user']

                        # Procura o socket do usuário correspondente a to_user
                        to_user_socket = self.nickname_to_socket.get(to_user)
                        if to_user_socket:
                            # Envia a solicitação de conexão para o usuário correspondente a to_user
                            request_message = json.dumps({
                                'tipo': 7,
                                'from_user': from_user,
                                'to_user': to_user
                            })
                            self.send_to_client(request_message, to_user_socket)

                elif message_data['tipo'] == 8:
                    with self.lock:
                        from_user = message_data['from_user']
                        to_user = message_data['to_user']
                        temp_server_port = message_data['temp_server_port']

                        # Procura o socket do usuário correspondente a to_user
                        to_user_socket = self.nickname_to_socket.get(to_user)
                        if to_user_socket:
                            # Envia a solicitação de conexão para o usuário correspondente a to_user
                            request_message = json.dumps({
                                'tipo': 8,
                                'from_user': from_user,
                                'to_user': to_user,
                                'temp_server_port': temp_server_port
                            })
                            self.send_to_client(request_message, to_user_socket)
                            
                elif message_data['tipo'] == 9:
                    with self.lock:
                        from_user = message_data['from_user']
                        to_user = message_data['to_user']

                        # Procura o socket do usuário correspondente a to_user
                        to_user_socket = self.nickname_to_socket.get(to_user)
                        if to_user_socket:
                            # Envia a solicitação de conexão para o usuário correspondente a to_user
                            request_message = json.dumps({
                                'tipo': 9,
                                'from_user': from_user,
                                'to_user': to_user
                            })
                            self.send_to_client(request_message, to_user_socket)
                

        except Exception as e:
            print(f"Erro ao lidar com o cliente: {e}")
        finally:
            client_socket.close()
            with self.lock:
                self.active_threads.remove(threading.current_thread())

            # Envia a lista de usuários online atualizada após a desconexão
            online_users_message = json.dumps({
                'tipo': 2,  # Tipo 2 indica mensagem de lista de usuários online
                'online_users': list(self.online_users)
            })
            self.broadcast_message(online_users_message)

    def find_user_socket(self, username):
        # Encontra o socket correspondente ao usuário pelo seu nome no dicionário
        with self.lock:
            return self.nickname_to_socket.get(username)

    def send_to_client(self, message, client_socket):

        tag = generate_tag(self.master_key, message)
        tag_str = binascii.hexlify(tag).decode('utf-8')

        message_text = json.dumps({
                'message': message,
                'tag': tag_str
            })
        
        messagem_criptografada = encrypt_message(self.master_key, message_text, self.master_nonce)
        message_str = binascii.hexlify(messagem_criptografada).decode('utf-8')
        
        try:
            client_socket.sendall(message_str.encode("utf-8"))
        except Exception as e:
            print(f"Erro ao enviar mensagem para um cliente: {e}")

    def broadcast_message(self, message):
        # Envia uma mensagem para todos os clientes conectados
        with self.lock:
            for client_socket in self.clients:
                # print(f"Enviando mensagem para:{self.clients}\n")
                try:
                    self.send_to_client(message, client_socket)
                    #client_socket.sendall(message.encode("utf-8"))
                except Exception as e:
                    print(f"Erro ao enviar mensagem para um cliente: {e}")

# Exemplo de uso
if __name__ == "__main__":
    chat_server = ChatServer()

    # Aguarda um input para encerrar o servidor
    input("Pressione Enter para encerrar o servidor...\n")

    # Chama a função para encerrar o servidor
    chat_server.stop_server()
