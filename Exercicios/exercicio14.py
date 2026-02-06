import sqlite3
from datetime import datetime


class Produto:
    def __init__(self, id=None, nome="", descricao="", quantidade=0, preco=0.0):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.quantidade = quantidade
        self.preco = preco


class Venda:
    def __init__(self, id=None, produto_id=None, quantidade=0, data_venda=None):
        self.id = id
        self.produto_id = produto_id
        self.quantidade = quantidade
        self.data_venda = data_venda or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class BancoDeDados:
    def __init__(self, nome_banco="estoque.db"):
        self.nome_banco = nome_banco
        self.conn = sqlite3.connect(self.nome_banco)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.criar_tabelas()

    def criar_tabelas(self):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                quantidade INTEGER NOT NULL,
                preco REAL NOT NULL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                data_venda TEXT NOT NULL,
                FOREIGN KEY (produto_id) REFERENCES Produtos(id)
            );
            """
        )

        self.conn.commit()

   
    def cadastrar_produto(self, produto: Produto):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO Produtos (nome, descricao, quantidade, preco)
            VALUES (?, ?, ?, ?)
            """,
            (produto.nome, produto.descricao, produto.quantidade, produto.preco),
        )
        self.conn.commit()
        print("✅ Produto cadastrado com sucesso!")

    def listar_produtos(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, nome, descricao, quantidade, preco FROM Produtos")
        produtos = cursor.fetchall()

        if not produtos:
            print("⚠️ Nenhum produto cadastrado.")
            return

        print("\n=== PRODUTOS CADASTRADOS ===")
        for p in produtos:
            print(
                f"ID: {p[0]} | Nome: {p[1]} | Quantidade: {p[3]} | Preço: R$ {p[4]:.2f}"
            )
            print(f"Descrição: {p[2]}")
            print("-" * 50)

    def atualizar_quantidade(self, produto_id: int, nova_quantidade: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Produtos SET quantidade = ? WHERE id = ?",
            (nova_quantidade, produto_id),
        )
        if cursor.rowcount == 0:
            print("⚠️ Produto não encontrado.")
        else:
            self.conn.commit()
            print("✅ Quantidade atualizada com sucesso!")

    def remover_produto(self, produto_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM Produtos WHERE id = ?", (produto_id,))
        if cursor.rowcount == 0:
            print("⚠️ Produto não encontrado.")
        else:
            self.conn.commit()
            print("✅ Produto removido com sucesso!")

    def buscar_produto_por_id(self, produto_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, nome, descricao, quantidade, preco FROM Produtos WHERE id = ?",
            (produto_id,),
        )
        row = cursor.fetchone()
        if row:
            return Produto(
                id=row[0],
                nome=row[1],
                descricao=row[2],
                quantidade=row[3],
                preco=row[4],
            )
        return None

    
    def registrar_venda(self, venda: Venda):
       
        produto = self.buscar_produto_por_id(venda.produto_id)
        if not produto:
            print("⚠️ Produto não encontrado. Venda não realizada.")
            return

        if venda.quantidade <= 0:
            print("⚠️ Quantidade de venda deve ser maior que zero.")
            return

        if produto.quantidade < venda.quantidade:
            print("⚠️ Quantidade insuficiente em estoque. Venda não realizada.")
            return

        
        nova_quantidade = produto.quantidade - venda.quantidade
        self.atualizar_quantidade(produto.id, nova_quantidade)

        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO Vendas (produto_id, quantidade, data_venda)
            VALUES (?, ?, ?)
            """,
            (venda.produto_id, venda.quantidade, venda.data_venda),
        )
        self.conn.commit()
        print("✅ Venda registrada com sucesso!")

    def listar_vendas(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT Vendas.id, Produtos.nome, Vendas.quantidade, Vendas.data_venda
            FROM Vendas
            JOIN Produtos ON Vendas.produto_id = Produtos.id
            ORDER BY Vendas.data_venda DESC
            """
        )
        vendas = cursor.fetchall()

        if not vendas:
            print("⚠️ Nenhuma venda registrada.")
            return

        print("\n=== VENDAS REGISTRADAS ===")
        for v in vendas:
            print(
                f"ID Venda: {v[0]} | Produto: {v[1]} | Quantidade: {v[2]} | Data: {v[3]}"
            )

    def fechar(self):
        self.conn.close()



def menu():
    print("\n=== SISTEMA DE ESTOQUE E VENDAS ===")
    print("1 - Cadastrar novo produto")
    print("2 - Listar produtos")
    print("3 - Atualizar quantidade de um produto")
    print("4 - Remover produto")
    print("5 - Registrar venda")
    print("6 - Listar vendas")
    print("0 - Sair")


def cadastrar_produto(db: BancoDeDados):
    print("\n=== CADASTRO DE PRODUTO ===")
    nome = input("Nome do produto: ")
    descricao = input("Descrição do produto: ")
    try:
        quantidade = int(input("Quantidade disponível: "))
        preco = float(input("Preço do produto (R$): "))
    except ValueError:
        print("⚠️ Quantidade e preço devem ser numéricos.")
        return

    produto = Produto(
        nome=nome,
        descricao=descricao,
        quantidade=quantidade,
        preco=preco,
    )
    db.cadastrar_produto(produto)


def atualizar_quantidade_produto(db: BancoDeDados):
    print("\n=== ATUALIZAÇÃO DE QUANTIDADE ===")
    try:
        produto_id = int(input("ID do produto: "))
        nova_quantidade = int(input("Nova quantidade disponível: "))
    except ValueError:
        print("⚠️ Valores inválidos.")
        return

    db.atualizar_quantidade(produto_id, nova_quantidade)


def remover_produto(db: BancoDeDados):
    print("\n=== REMOÇÃO DE PRODUTO ===")
    try:
        produto_id = int(input("ID do produto a remover: "))
    except ValueError:
        print("⚠️ ID inválido.")
        return

    db.remover_produto(produto_id)


def registrar_venda_menu(db: BancoDeDados):
    print("\n=== REGISTRAR VENDA ===")
    try:
        produto_id = int(input("ID do produto vendido: "))
        quantidade = int(input("Quantidade vendida: "))
    except ValueError:
        print("⚠️ Valores inválidos.")
        return

    venda = Venda(produto_id=produto_id, quantidade=quantidade)
    db.registrar_venda(venda)



def main():
    db = BancoDeDados()

    while True:
        menu()
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_produto(db)
        elif opcao == "2":
            db.listar_produtos()
        elif opcao == "3":
            atualizar_quantidade_produto(db)
        elif opcao == "4":
            remover_produto(db)
        elif opcao == "5":
            registrar_venda_menu(db)
        elif opcao == "6":
            db.listar_vendas()
        elif opcao == "0":
            print("Encerrando o sistema. Até mais!")
            db.fechar()
            break
        else:
            print("⚠️ Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
