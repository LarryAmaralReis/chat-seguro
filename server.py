import socket
import threading
import json

class ChatServer:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 20000
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = set()
        self.online_users = set()  # Agora usa um conjunto para garantir usuários únicos
        self.lock = threading.Lock()
        self.active_threads = set()

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

                print(f"Mensagem recebida do cliente {client_socket.getpeername()}: {data}")

                # Lógica de tratamento de mensagem aqui

                message_data = json.loads(data)

                if message_data['tipo'] == 1:  # Tipo 1 indica mensagem de entrada
                    with self.lock:
                        self.online_users.add(message_data['nickname'])

                    # Envia a lista de usuários online para todos os clientes
                    online_users_message = json.dumps({
                        'tipo': 2,  # Tipo 2 indica mensagem de lista de usuários online
                        'online_users': list(self.online_users)
                    })
                    print(f"DIC ONLINE USERS: {online_users_message}")
                    self.broadcast_message(online_users_message)

                elif message_data['tipo'] == 10:
                    with self.lock:
                        self.online_users.remove(message_data['nickname'])
                    
                    # Envia a lista de usuários online para todos os clientes
                    online_users_message = json.dumps({
                        'tipo': 10,  # Tipo 2 indica mensagem de lista de usuários online
                        'online_users': list(self.online_users)
                    })
                    print(f"DIC ONLINE USERS: {online_users_message}")
                    self.broadcast_message(online_users_message)

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

    def broadcast_message(self, message):
        # Envia uma mensagem para todos os clientes conectados
        with self.lock:
            for client_socket in self.clients:
                # print(f"Enviando mensagem para:{self.clients}\n")
                try:
                    client_socket.sendall(message.encode("utf-8"))
                except Exception as e:
                    print(f"Erro ao enviar mensagem para um cliente: {e}")

# Exemplo de uso
if __name__ == "__main__":
    chat_server = ChatServer()

    # Aguarda um input para encerrar o servidor
    input("Pressione Enter para encerrar o servidor...\n")

    # Chama a função para encerrar o servidor
    chat_server.stop_server()
