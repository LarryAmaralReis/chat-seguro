from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

def perform_dh_key_exchange():
    parameters = dh.generate_parameters(generator=2, key_size=2048, backend=default_backend())
    
    private_key_alice = parameters.generate_private_key()
    public_key_alice = private_key_alice.public_key()

    private_key_bob = parameters.generate_private_key()
    public_key_bob = private_key_bob.public_key()

    shared_key_alice = private_key_alice.exchange(public_key_bob)
    shared_key_bob = private_key_bob.exchange(public_key_alice)

    return shared_key_alice, shared_key_bob

def derive_chacha20_key(shared_key, nonce):
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes for a 256-bit key
        salt=None,
        info=b'chacha20 key derivation',
        backend=default_backend()
    )
    return hkdf.derive(shared_key + nonce)

def encrypt_message(message, key, nonce):
    chacha_key = derive_chacha20_key(key, nonce)

    cipher = Cipher(algorithms.ChaCha20(chacha_key, nonce), mode=None, backend=default_backend())

    encryptor = cipher.encryptor()

    ciphertext = encryptor.update(message) + encryptor.finalize()

    return ciphertext

def decrypt_message(ciphertext, key, nonce):
    # Derive a key for ChaCha20
    chacha_key = derive_chacha20_key(key, nonce)

    # Initialize the ChaCha20 cipher
    cipher = Cipher(algorithms.ChaCha20(chacha_key, nonce), mode=None, backend=default_backend())

    # Create the decryptor object
    decryptor = cipher.decryptor()

    # Decrypt the message
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    return plaintext

nonce = urandom(16)

print(f"Tipo do nonce: {type(nonce)}")

shared_key_alice, shared_key_bob = perform_dh_key_exchange()

message_from_alice = b"Hello, Bob! This is a secret message."

ciphertext = encrypt_message(message_from_alice, shared_key_alice, nonce)

decrypted_message = decrypt_message(ciphertext, shared_key_bob, nonce)

print(f"Original Message: {message_from_alice}")
print(f"Tipo da mensagem: {type(message_from_alice)}")
print(f"Ciphertext: {ciphertext.hex()}")
print(f"Decrypted Message by Bob: {decrypted_message.decode('utf-8')}")
print(f"Tipo da mensagem decriptada: {type(decrypted_message.decode('utf-8'))}")