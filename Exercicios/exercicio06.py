PRIORIDADES = ("baixa", "média", "alta")  # tupla
tarefas = []  # lista de tarefas (cada tarefa é um dicionário)
categorias_usadas = set()  # conjunto de categorias já usadas


def exibir_tarefa(tarefa):
    status = "✅ Concluída" if tarefa["concluida"] else "⏳ Pendente"
    print(f"\nID: {tarefa['id']}")
    print(f"Nome: {tarefa['nome']}")
    print(f"Descrição: {tarefa['descricao']}")
    print(f"Prioridade: {tarefa['prioridade']}")
    print(f"Categoria: {tarefa['categoria']}")
    print(f"Status: {status}")


def adicionar_tarefa(tarefas, proximo_id):
    print("\n=== Adicionar nova tarefa ===")
    nome = input("Nome da tarefa: ")
    descricao = input("Descrição da tarefa: ")
    print("Prioridades possíveis: baixa, média, alta")
    prioridade = input("Prioridade da tarefa: ").strip().lower()

    if prioridade not in PRIORIDADES:
        print("Prioridade inválida! Usando 'baixa' como padrão.")
        prioridade = "baixa"

    categoria = input("Categoria da tarefa: ")

    tarefa = {
        "id": proximo_id,
        "nome": nome,
        "descricao": descricao,
        "prioridade": prioridade,
        "categoria": categoria,
        "concluida": False
    }

    tarefas.append(tarefa)
    categorias_usadas.add(categoria)

    print(f"\nTarefa '{nome}' adicionada com sucesso com ID {proximo_id}!")
    return proximo_id + 1


def listar_tarefas(tarefas):
    print("\n=== Lista de tarefas ===")
    if not tarefas:
        print("Nenhuma tarefa cadastrada.")
        return

    for tarefa in tarefas:
        exibir_tarefa(tarefa)


def listar_por_prioridade(tarefas):
    print("\n=== Filtrar tarefas por prioridade ===")
    print("Prioridades possíveis: baixa, média, alta")
    prioridade = input("Digite a prioridade desejada: ").strip().lower()

    if prioridade not in PRIORIDADES:
        print("Prioridade inválida.")
        return

    encontradas = [t for t in tarefas if t["prioridade"] == prioridade]

    if not encontradas:
        print(f"Nenhuma tarefa com prioridade '{prioridade}'.")
        return

    for tarefa in encontradas:
        exibir_tarefa(tarefa)


def listar_por_categoria(tarefas):
    print("\n=== Filtrar tarefas por categoria ===")
    if not categorias_usadas:
        print("Nenhuma categoria cadastrada ainda.")
        return

    print("Categorias existentes:")
    for cat in categorias_usadas:
        print(f"- {cat}")

    categoria = input("Digite a categoria desejada: ")

    encontradas = [t for t in tarefas if t["categoria"] == categoria]

    if not encontradas:
        print(f"Nenhuma tarefa na categoria '{categoria}'.")
        return

    for tarefa in encontradas:
        exibir_tarefa(tarefa)


def marcar_concluida(tarefas):
    print("\n=== Marcar tarefa como concluída ===")
    if not tarefas:
        print("Nenhuma tarefa cadastrada.")
        return

    try:
        id_busca = int(input("Digite o ID da tarefa a concluir: "))
    except ValueError:
        print("ID inválido.")
        return

    for tarefa in tarefas:
        if tarefa["id"] == id_busca:
            if tarefa["concluida"]:
                print("Essa tarefa já está concluída.")
            else:
                tarefa["concluida"] = True
                print(f"Tarefa '{tarefa['nome']}' marcada como concluída!")
            return

    print("Nenhuma tarefa encontrada com esse ID.")


def listar_pendentes(tarefas):
    print("\n=== Tarefas pendentes ===")
    pendentes = [t for t in tarefas if not t["concluida"]]

    if not pendentes:
        print("Não há tarefas pendentes.")
        return

    for tarefa in pendentes:
        exibir_tarefa(tarefa)


def mostrar_menu():
    print("\n=== GERENCIADOR DE TAREFAS ===")
    print("1 - Adicionar tarefa")
    print("2 - Listar todas as tarefas")
    print("3 - Marcar tarefa como concluída")
    print("4 - Listar tarefas por prioridade")
    print("5 - Listar tarefas por categoria")
    print("6 - Listar apenas tarefas pendentes")
    print("0 - Sair")


def main():
    proximo_id = 1

    while True:
        mostrar_menu()
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            proximo_id = adicionar_tarefa(tarefas, proximo_id)
        elif opcao == "2":
            listar_tarefas(tarefas)
        elif opcao == "3":
            marcar_concluida(tarefas)
        elif opcao == "4":
            listar_por_prioridade(tarefas)
        elif opcao == "5":
            listar_por_categoria(tarefas)
        elif opcao == "6":
            listar_pendentes(tarefas)
        elif opcao == "0":
            print("Saindo... Até mais!")
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
