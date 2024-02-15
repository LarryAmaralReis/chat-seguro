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
        
    def send_to_private(self, data_dict, socket, address):
        try:
            if socket and socket.fileno() != -1:
                json_data = json.dumps(data_dict)
                socket.sendto(json_data.encode("utf-8"),address)
        except Exception as e:
            print(f"Erro ao enviar dados privados: {e}")

    def handle_client(self, client_socket, channel_port):
        try:
            while True:
                data, address = client_socket.recvfrom(1024)
                if not data:
                    break

                print(f"Mensagem recebida do cliente {address} no canal {channel_port}: {data}")

                data = json.loads(data)
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
