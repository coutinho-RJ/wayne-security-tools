class ContaBancaria:
    def __init__(self, titular, saldo_inicial=0):
        self._titular = titular
        self._saldo = saldo_inicial

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print(f"Depósito de R$ {valor:.2f} realizado com sucesso!")
        else:
            print("O valor do depósito deve ser positivo.")

    def sacar(self, valor):
        if valor <= 0:
            print("O valor do saque deve ser positivo.")
        elif valor > self._saldo:
            print("Saldo insuficiente para realizar o saque.")
        else:
            self._saldo -= valor
            print(f"Saque de R$ {valor:.2f} realizado com sucesso!")

    def exibir_saldo(self):
        print(f"Titular: {self._titular} | Saldo atual: R$ {self._saldo:.2f}")


# --------------------------
#  SISTEMA DE INTERAÇÃO
# --------------------------
print("=== SISTEMA BANCÁRIO ===")

nome = input("Digite o nome do titular da conta: ")
conta = ContaBancaria(nome)

while True:
    print("\n--- MENU ---")
    print("1 - Depositar")
    print("2 - Sacar")
    print("3 - Exibir saldo")
    print("4 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        valor = float(input("Valor do depósito: R$ "))
        conta.depositar(valor)

    elif opcao == "2":
        valor = float(input("Valor do saque: R$ "))
        conta.sacar(valor)

    elif opcao == "3":
        conta.exibir_saldo()

    elif opcao == "4":
        print("Encerrando o sistema. Até mais!")
        break

    else:
        print("Opção inválida. Tente novamente.")
