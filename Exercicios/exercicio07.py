import random

def lancar_dados():
    dado1 = random.randint(1, 6)
    dado2 = random.randint(1, 6)
    return dado1 + dado2

# Exemplo de uso:
resultado = lancar_dados()
print("Resultado do lançamento:", resultado)
