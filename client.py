import socket
import threading

DISCONNECT_MESSAGE = "!disconnect"

def receive_messages(client_socket):
    try:
        while True:
            message = client_socket.recv(1024)
            print(message.decode())
    except Exception as e:
        print(f"Erro ao receber mensagens: {e}")

def main():
    host = '127.0.0.1'
    port = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Solicita e envia o nickname ao servidor
    nickname = input("Digite seu nickname: ")
    client_socket.send(nickname.encode())

    # Inicia uma thread para receber mensagens
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    try:
        while True:
            message = input()
            
            # Verifica se é o comando de desconexão
            if message == DISCONNECT_MESSAGE:
                print("Desconectando...")
                client_socket.send(message.encode())
                break

            client_socket.send(message.encode())
    except KeyboardInterrupt:
        print("Encerrando o cliente.")
        client_socket.send(DISCONNECT_MESSAGE.encode())

if __name__ == "__main__":
    main()
