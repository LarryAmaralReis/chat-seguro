import socket
import threading
import json
from functions import *
from os import urandom
import binascii

class ChatChannels:
    def __init__(self, host='127.0.0.1', ports=[20001, 20002, 20003]):
        self.HOST = host
        self.PORTS = ports
        self.channels = {port: {} for port in ports}

        #------------------------------#
        self.master_key = 54454969524667022591300178147674637787134628051833060362233619131391366951278
        self.master_nonce = b'Z\x06\x98p#Z\xab\xc3\x81\x91\xf0\xec1\xb8\x03?'
        #------------------------------#
        
    def send_to_private(self, data_dict, socket, address):

        message = json.dumps(data_dict)

        tag = generate_tag(self.master_key, message)
        tag_str = binascii.hexlify(tag).decode('utf-8')

        message_text = json.dumps({
                'message': message,
                'tag': tag_str
            })
        
        messagem_criptografada = encrypt_message(self.master_key, message_text, self.master_nonce)
        message_str = binascii.hexlify(messagem_criptografada).decode('utf-8')

        try:
            if socket and socket.fileno() != -1:
                socket.sendto(message_str.encode("utf-8"),address)
        except Exception as e:
            print(f"Erro ao enviar dados privados: {e}")

    def handle_client(self, client_socket, channel_port):
        try:
            while True:
                data, address = client_socket.recvfrom(1024)
                if not data:
                    break

                mensagem_criptografada = binascii.unhexlify(data)
                mensagem = decrypt_message(self.master_key, mensagem_criptografada, self.master_nonce)
                data = json.loads(mensagem)
                tag = binascii.unhexlify(data['tag'])
                received_data = json.loads(data['message'])
                received_data_tag = json.dumps(received_data)

                verify_tag(self.master_key, received_data_tag, tag)

                print(f"Mensagem recebida do cliente {address} no canal {channel_port}: {data['message']}")

                data = received_data
                if data['tipo'] == 21:
                    self.channels[channel_port][data['nickname']] = {'udp_address': data['udp_address'],}

                    message = {
                        'tipo': 22,
                        'nickname:': [channel_port],
                        'new_user': data['nickname'],
                        'channel_users': list(self.channels[channel_port])
                    }
                    
                    for client, client_data in self.channels[channel_port].copy().items():
                        self.send_to_private(message, client_socket, tuple(client_data['udp_address']))
                
                if data['tipo'] == 31:
                    del self.channels[channel_port][data['nickname']]

                    message = {
                        'tipo': 32,
                        'nickname:': [channel_port],
                        'old_user': data['nickname'],
                        'channel_users': list(self.channels[channel_port])
                    }

                    for client, client_data in self.channels[channel_port].copy().items():
                        self.send_to_private(message, client_socket, tuple(client_data['udp_address']))

        except Exception as e:
            pass
            #print(f"Erro ao lidar com o cliente {address} no canal {channel_port}: {e}")
        finally:
            del self.channels[channel_port][data['nickname']]
            client_socket.close()

    def create_channel(self, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.HOST, port))

        print(f"Canal escutando em {self.HOST}:{port}")

        while True:
            client_handler = threading.Thread(target=self.handle_client, args=(server_socket, port))
            client_handler.start()

    def start_channels(self):
        threads = [threading.Thread(target=self.create_channel, args=(port,)) for port in self.PORTS]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    chat_channels = ChatChannels()
    chat_channels.start_channels()
