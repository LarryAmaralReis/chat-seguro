from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from dh import *

def generate_dh_key_pair(prime=None):
    # Gera uma chave DH (Diffie-Hellman)
    base = 2

    # Se prime não for fornecido, gera um número primo aleatório
    if prime is None:
        prime = generate_prime()

    # Gera uma chave privada aleatória
    private_key = generate_private_key()

    # Calcula a chave pública
    public_key = generate_public_key(private_key, base, prime)

    return private_key, public_key, prime

def key_exchange(private_key, public_key, prime):
    # Calcula a chave secreta compartilhada
    shared_key = calculate_shared_secret(private_key, public_key, prime)

    return shared_key

def encrypt_message(key, message, nonce):
    # Criptografa a mensagem usando ChaCha20
    key_bytes = key.to_bytes((key.bit_length() + 7) // 8, byteorder='big')
    cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
    return ciphertext

def decrypt_message(key, ciphertext, nonce):
    # Descriptografa a mensagem usando ChaCha20
    key_bytes = key.to_bytes((key.bit_length() + 7) // 8, byteorder='big')
    cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_message = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_message.decode()
