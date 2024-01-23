import socket
import threading
import json
from dh import *
from functions import *
from os import urandom
import binascii

class ChatChannels:
    def __init__(self, host='127.0.0.1', ports=[20001, 20002, 20003]):
        self.HOST = host
        self.PORTS = ports
        self.channels = {port: {} for port in ports}


        #Informações importantes
        self.channel_info = {port: {'private_key': None, 'public_key': None, 'nonce': None, 'prime': None} for port in ports}


        #Informações temporárias
        self.client_public_key = None
        self.channel_shared_key = None
        self.temp_server_socket = None

    def json_message(self, tipo, channel, nickname, message):
        if message:
            message_data = {
                'tipo': tipo,
                'channel': channel,
                'nickname': nickname,
                'message': message
            }
            json_data = json.dumps(message_data)
            return json_data
        
    def send_to_private(self, data_dict, socket):
        try:
            if socket and socket.fileno() != -1:
                json_data = json.dumps(data_dict)
                socket.sendall(json_data.encode("utf-8"))
        except Exception as e:
            pass
            #print(f"Erro ao enviar dados privados: {e}")

    def handle_client(self, client_socket, address, channel_port):
        try:
            while True:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break

                print(f"Mensagem recebida do cliente {address} no canal {channel_port}: {data}")

                message_data = json.loads(data)
                if message_data['tipo'] == 200:
                    self.client_public_key = message_data['client_public_key']
                    self.channel_shared_key = key_exchange(self.channel_info[channel_port]['private_key'], self.client_public_key, self.channel_info[channel_port]['prime'])
                    print(f"Chave compartilhada do canal/cliente:{self.channel_shared_key}")

                    self.channels[channel_port][client_socket] = {'nickname': message_data['nickname'], 'channel_shared_key': self.channel_shared_key}

                    for client, client_data in self.channels[channel_port].copy().items():
                        pass
                        #print(f"Um dos clientes: {client}")

                elif message_data['tipo'] == 6:
                    mensagem_criptografada = binascii.unhexlify(message_data['message'])
                    for client, client_data in self.channels[channel_port].copy().items():
                        if client == client_socket:
                            shared_key = client_data['channel_shared_key']
                    mensagem = decrypt_message(shared_key, mensagem_criptografada, self.channel_info[channel_port]['nonce'])
                    for client, client_data in self.channels[channel_port].copy().items():
                        if client != client_socket:
                            try:
                                if client.fileno() != -1:
                                    messagem_criptografada = encrypt_message(client_data['channel_shared_key'], mensagem, self.channel_info[channel_port]['nonce'])
                                    message_text = binascii.hexlify(messagem_criptografada).decode('utf-8')
                                    json_data = self.json_message(message_data['tipo'], message_data['channel'], message_data['nickname'], message_text)
                                    client.send(bytes(json_data, "utf-8"))
                            except (socket.error, OSError):
                                del self.channels[channel_port][client]
                    break
                else:
                    mensagem_criptografada = binascii.unhexlify(message_data['message'])
                    for client, client_data in self.channels[channel_port].copy().items():
                        if client == client_socket:
                            shared_key = client_data['channel_shared_key']
                    mensagem = decrypt_message(shared_key, mensagem_criptografada, self.channel_info[channel_port]['nonce'])
                    for client, client_data in self.channels[channel_port].copy().items():
                        if client != client_socket:
                            try:
                                messagem_criptografada = encrypt_message(client_data['channel_shared_key'], mensagem, self.channel_info[channel_port]['nonce'])
                                message_text = binascii.hexlify(messagem_criptografada).decode('utf-8')
                                json_data = self.json_message(message_data['tipo'], message_data['channel'], message_data['nickname'], message_text)
                                client.send(bytes(json_data, "utf-8"))
                            except:
                                 del self.channels[channel_port][client]
        except Exception as e:
            pass
            #print(f"Erro ao lidar com o cliente {address} no canal {channel_port}: {e}")
        finally:
            del self.channels[channel_port][client_socket]
            client_socket.close()

    def create_channel(self, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.HOST, port))
        server_socket.listen(5)

        print(f"Canal escutando em {self.HOST}:{port}")

        channel_private_key, channel_public_key, prime = generate_dh_key_pair()
        nonce = urandom(16)
        aux = nonce
        self.channel_info[port]['private_key'] = channel_private_key
        self.channel_info[port]['public_key'] = channel_public_key
        self.channel_info[port]['prime'] = prime
        self.channel_info[port]['nonce'] = binascii.hexlify(nonce).decode('utf-8')

        dados = {
                'tipo': 200,
                'nickname': port,
                'prime': self.channel_info[port]['prime'],
                'channel_public_key': self.channel_info[port]['public_key'],
                'nonce': self.channel_info[port]['nonce']
            }
        print(f"Self.Nonce: {aux}")
        print(f"Self.Prime: {self.channel_info[port]['prime']}")

        while True:
            client_socket, address = server_socket.accept()
            print(f"Conexão aceita de {address} no canal {port}")

            self.temp_server_socket = client_socket

            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, address, port))
            client_handler.start()

            self.send_to_private(dados, self.temp_server_socket)
            self.channel_info[port]['nonce']  = aux

    def start_channels(self):
        threads = [threading.Thread(target=self.create_channel, args=(port,)) for port in self.PORTS]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    chat_channels = ChatChannels()
    chat_channels.start_channels()
