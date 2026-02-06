import flet as ft


def main(page: ft.Page):
    page.title = "Lista de Tarefas"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"

    campo_tarefa = ft.TextField(
        label="Digite uma tarefa",
        width=300
    )

    lista_tarefas = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        auto_scroll=True
    )

    def adicionar_tarefa(e):
        texto = campo_tarefa.value.strip()
        if texto:
            lista_tarefas.controls.append(ft.Text(texto))
            campo_tarefa.value = ""
            page.update()

    botao_adicionar = ft.Button(
        "Adicionar",           # <- agora o texto vai aqui, sem text=
        on_click=adicionar_tarefa
    )

    page.add(
        ft.Column(
            controls=[
                campo_tarefa,
                botao_adicionar,
                ft.Text("Tarefas:", size=20, weight="bold"),
                lista_tarefas
            ],
            width=400
        )
    )


if __name__ == "__main__":
    ft.run(main)   # <- no lugar de ft.app(target=main)

