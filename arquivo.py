from os import urandom
import binascii

nonce = urandom(16)

hex_nonce = binascii.hexlify(nonce)

# Convertendo representação hexadecimal de volta para bytes
decoded_nonce_bytes = binascii.unhexlify(hex_nonce)

print(f'Original Bytes: {nonce}')
print(f'Hexadecimal: {hex_nonce}')
print(f'Decoded Bytes: {decoded_nonce_bytes}')
