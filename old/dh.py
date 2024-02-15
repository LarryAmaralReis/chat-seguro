import random
import hashlib

def is_prime(n, k=5):
    """Verifica se um número é primo usando o teste de Miller-Rabin."""
    if n <= 1:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    # Escreve n-1 como 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Testa k vezes
    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def generate_prime(bits=256):
    """Gera um número primo aleatório com o número especificado de bits."""
    while True:
        num = random.getrandbits(bits)
        if is_prime(num):
            return num

def generate_private_key(bits=256):
    """Gera uma chave privada aleatória."""
    return random.randint(2**(bits-1), 2**bits - 1)

def generate_public_key(private_key, base, prime):
    """Calcula a chave pública."""
    return pow(base, private_key, prime)

def calculate_shared_secret(private_key, other_public_key, prime):
    """Calcula a chave secreta compartilhada."""
    return pow(other_public_key, private_key, prime)


# Parâmetros públicos compartilhados
base = 2

# Gera números primos grandes para garantir segurança
prime = generate_prime()

# Parte A
private_key_A = generate_private_key()
public_key_A = generate_public_key(private_key_A, base, prime)

# Parte B
private_key_B = generate_private_key()
public_key_B = generate_public_key(private_key_B, base, prime)

# Troca de chaves públicas
shared_secret_A = calculate_shared_secret(private_key_A, public_key_B, prime)
shared_secret_B = calculate_shared_secret(private_key_B, public_key_A, prime)

# Verificação
# print("Chave secreta compartilhada (A):", shared_secret_A)
# print("Chave secreta compartilhada (B):", shared_secret_B)
