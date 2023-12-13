import socket
import threading

DISCONNECT_MESSAGE = "!disconnect"
SHUTDOWN_MESSAGE = "!shutdown"
EXPULSAR_COMMAND = "!expulsar"

def broadcast_message(message, sender_socket, clients):
    # Envia a mensagem para todos os clientes, exceto o remetente
    for client, _ in clients:
        if client != sender_socket:
            try:
                client.send(message.encode())
            except Exception as e:
                print(f"Erro ao enviar mensagem para um cliente: {e}")

def handle_expulsar_command(command, clients):
    try:
        # Obtém o endereço IP e a porta do cliente a ser desconectado
        ip_port_to_expulsar = command.split(" ")[1]
        expulsar_client = next((client, nick) for client, nick in clients if f"{client.getpeername()[0]}:{client.getpeername()[1]}" == ip_port_to_expulsar)
        expulsar_socket, expulsar_nickname = expulsar_client

        # Envia mensagem de expulsão ao cliente
        expulsar_message = f"Você foi desconectado pelo administrador."
        expulsar_socket.send(expulsar_message.encode())

        # Remove o cliente da lista
        clients.remove((expulsar_socket, expulsar_nickname))
        print(f"{expulsar_nickname} foi expulso.")

        # Envia mensagem de expulsão aos outros clientes
        expulsar_broadcast = f"{expulsar_nickname} foi expulso pelo administrador."
        broadcast_message(expulsar_broadcast, None, clients)
    except Exception as e:
        print(f"Erro ao expulsar cliente: {e}")

def handle_client(client_socket, address, clients):
    try:
        # Recebe o nickname do cliente ao se conectar
        nickname = client_socket.recv(1024).decode()
        print(f"{address[0]}:{address[1]} se conectou como {nickname}")

        # Adiciona o cliente e seu nickname à lista
        clients.append((client_socket, nickname))

        while True:
            message = client_socket.recv(1024)
            if not message:
                break

            # Verifica se é um comando de desconexão
            if message.decode() == DISCONNECT_MESSAGE:
                break

            # Formata a mensagem com o endereço IP, nickname e conteúdo
            formatted_message = f"[{address[0]}:{address[1]} | {nickname}]: {message.decode()}"

            # Exibe a mensagem no terminal do servidor
            print(formatted_message)

            # Encaminha a mensagem para todos os outros clientes
            broadcast_message(formatted_message, client_socket, clients)

            # Verifica se é um comando de shutdown
            if message.decode() == SHUTDOWN_MESSAGE:
                break

            # Verifica se é um comando de expulsar
            if message.decode().startswith(EXPULSAR_COMMAND):
                handle_expulsar_command(message.decode(), clients)
    except Exception as e:
        print(f"Erro ao lidar com cliente {address}: {e}")
    finally:
        # Remove o cliente da lista quando desconectar
        clients.remove((client_socket, nickname))
        print(f"{nickname} desconectou.")

        # Envia mensagem de desconexão aos outros clientes
        disconnect_message = f"{nickname} se desconectou."
        broadcast_message(disconnect_message, None, clients)

        client_socket.close()


def handle_commands(server_socket, clients):
    while True:
        command = input("Digite um comando para enviar aos clientes (ou '!shutdown' para encerrar o servidor): ")
        if command.lower() == '!shutdown':
            # Envia o comando formatado como uma mensagem para todos os clientes
            broadcast_message("[Server]: Server will shutdown. Goodbye!", None, clients)

            # Aguarda um pouco para os clientes receberem a mensagem
            threading.Event().wait(2)

            # Encerra o servidor e desconecta todos os clientes
            for client_socket, _ in clients:
                try:
                    client_socket.send(SHUTDOWN_MESSAGE.encode())
                    client_socket.close()
                except Exception as e:
                    print(f"Erro ao desconectar cliente: {e}")

            # Encerra o socket do servidor
            server_socket.close()

            break
        else:
            # Verifica se é um comando iniciado por '!' e não envia aos clientes
            if command.startswith('!'):
                print(f"Comando '{command}' não enviado aos clientes.")
            else:
                # Envia o comando como uma mensagem para todos os clientes
                broadcast_message(f"[Server]: {command}", None, clients)

def main():
    host = '127.0.0.1'
    port = 12345

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    clients = []

    # Inicia a thread para lidar com os comandos do usuário
    command_thread = threading.Thread(target=handle_commands, args=(server_socket, clients))
    command_thread.start()

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")

            # Inicia uma thread para lidar com o cliente
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, clients))
            client_handler.start()

        # Aguarda a conclusão das threads de comando e cliente
        command_thread.join()
    except KeyboardInterrupt:
        print("Encerrando o servidor...")

        # Envia mensagem de desligamento aos clientes
        broadcast_message("O servidor foi desconectado.", None, clients)

        # Aguarda as threads dos clientes serem encerradas
        for client_socket, _ in clients:
            try:
                client_socket.send(SHUTDOWN_MESSAGE.encode())
                client_socket.close()
            except Exception as e:
                print(f"Erro ao desconectar cliente: {e}")

        # Encerra o socket do servidor
        server_socket.close()

if __name__ == "__main__":
    main()
