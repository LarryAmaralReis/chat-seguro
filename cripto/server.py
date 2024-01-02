import socket
from functions import *
from os import urandom

def main():
    # Configuração do servidor
    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()

        print(f"Servidor ouvindo em {host}:{port}")

        conn, addr = server_socket.accept()
        print(f"Conexão recebida de {addr}")

        # Gera chaves Diffie-Hellman
        server_private_key, server_public_key, prime = generate_dh_key_pair()

        nonce = urandom(16)

        conn.sendall(str(prime).encode('utf-8'))

        conn.sendall(str(server_public_key).encode('utf-8'))

        conn.sendall(nonce)

        # Recebe a chave pública do cliente
        received_public_key_bytes = conn.recv(4096)
        received_public_key = int(received_public_key_bytes.decode())

        # Troca de chaves
        shared_key = key_exchange(int(server_private_key), int(received_public_key), prime)

        while True:
            # Recebe a mensagem criptografada
            encrypted_message = conn.recv(4096)
            if not encrypted_message:
                break

            # Descriptografa e exibe a mensagem
            decrypted_message = decrypt_message(shared_key, encrypted_message, nonce)
            print(f"Mensagem recebida: {decrypted_message}")

            # Envia uma mensagem criptografada de volta
            message_to_send = input("Digite uma mensagem para enviar: ")
            encrypted_message_to_send = encrypt_message(shared_key, message_to_send, nonce)
            conn.sendall(encrypted_message_to_send)

if __name__ == "__main__":
    main()
