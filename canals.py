import socket
import threading
import json

# Configuração do servidor
HOST = '127.0.0.1'
PORTS = [20001, 20002, 20003]  # Lista de portas para os três canais

# Dicionário para armazenar clientes em cada canal
channels = {port: set() for port in PORTS}

# Função para lidar com a comunicação de um cliente em um canal específico
def handle_client(client_socket, address, channel_port):
    try:
        # Adiciona o cliente ao canal correspondente
        channels[channel_port].add(client_socket)

        message = json_message(1, None,'[Server]', f"Bem-vindo ao canal {channel_port}!\n")
        client_socket.send(bytes(message, "utf-8"))

        # Lida com a comunicação no canal
        while True:
            # Recebe a mensagem do cliente
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            print(f"Mensagem recebida do cliente {address} no canal {channel_port}: {data}")

            # Converte a mensagem JSON para um dicionário
            message_data = json.loads(data)
            if message_data['tipo'] == 6:
                # Mensagem de desconexão, remove o cliente do canal
                # channels[channel_port].remove(client_socket)
                json_data = json.dumps(message_data)
                for client in channels[channel_port].copy():
                    if client != client_socket:
                        try:
                            # Envia a mensagem apenas se o socket ainda estiver conectado
                            if client.fileno() != -1:
                                client.send(bytes(json_data, "utf-8"))
                        except (socket.error, OSError):
                            # Remove clientes desconectados ou com erro
                            channels[channel_port].remove(client)
                break
            else:
                # Outras mensagens, envia para os outros clientes no canal
                json_data = json.dumps(message_data)
                for client in channels[channel_port].copy():
                    if client != client_socket:
                        try:
                            client.send(bytes(json_data, "utf-8"))
                        except:
                            channels[channel_port].remove(client)
    except Exception as e:
        print(f"Erro ao lidar com o cliente {address} no canal {channel_port}: {e}")
    finally:
        channels[channel_port].remove(client_socket)
        client_socket.close()


# Função principal para criar sockets em diferentes portas
def create_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, port))
    server_socket.listen(5)

    print(f"Canal escutando em {HOST}:{port}")

    # Aceita e lida com as conexões de clientes
    while True:
        client_socket, address = server_socket.accept()
        print(f"Conexão aceita de {address} no canal {port}")

        # Cria uma nova thread para lidar com o cliente no canal específico
        client_handler = threading.Thread(target=handle_client, args=(client_socket, address, port))
        client_handler.start()
        
def json_message(tipo, channel, nickname, message):
        if message:
            message_data = {
                'tipo': tipo,
                'channel': channel,
                'nickname': nickname,
                'message': message
            }
            json_data = json.dumps(message_data)
        return json_data

# Inicia os servidores em diferentes portas usando threads separadas
threads = [threading.Thread(target=create_server, args=(port,)) for port in PORTS]
for thread in threads:
    thread.start()

# Aguarda a conclusão de todas as threads
for thread in threads:
    thread.join()
