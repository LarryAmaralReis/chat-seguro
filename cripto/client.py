import socket
from functions import *

def main():
    # Configuração do cliente
    host = 'localhost'
    port = 12345

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))

        print(f"Conectado a {host}:{port}")

        # Recebe o número primo do servidor
        received_prime_bytes = client_socket.recv(4096)
        received_prime = int(received_prime_bytes.decode('utf-8'))

        received_public_key_bytes = client_socket.recv(4096)
        received_public_key = int(received_public_key_bytes.decode('utf-8'))

        # Gera chaves Diffie-Hellman
        client_private_key, client_public_key, _ = generate_dh_key_pair(received_prime)

        client_public_key_bytes = str(client_public_key).encode('utf-8')
        client_socket.sendall(client_public_key_bytes)

        # Troca de chaves
        shared_key = key_exchange(client_private_key, received_public_key, received_prime)

        nonce = client_socket.recv(4096)
        
        while True:
            # Envia uma mensagem criptografada
            message_to_send = input("Digite uma mensagem para enviar: ")
            encrypted_message_to_send = encrypt_message(shared_key, message_to_send, nonce)
            client_socket.sendall(encrypted_message_to_send)

            # Recebe a mensagem criptografada
            encrypted_message = client_socket.recv(4096)
            if not encrypted_message:
                break

            # Descriptografa e exibe a mensagem
            decrypted_message = decrypt_message(shared_key, encrypted_message, nonce)
            print(f"Mensagem recebida: {decrypted_message}")

if __name__ == "__main__":
    main()
