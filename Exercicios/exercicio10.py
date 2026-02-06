import flet as ft

def main(page: ft.Page):
    page.title = "Formulário de Contato"
    page.padding = 20
    page.vertical_alignment = "start"

    nome = ft.TextField(label="Nome", width=400)
    email = ft.TextField(label="Email", width=400)
    mensagem = ft.TextField(label="Mensagem", width=400, multiline=True, min_lines=3)

    confirmacao = ft.Text("", color="green")

    def enviar_formulario(e):
        if nome.value.strip() and email.value.strip() and mensagem.value.strip():
            confirmacao.value = "Formulário enviado com sucesso!"
            nome.value = ""
            email.value = ""
            mensagem.value = ""
        else:
            confirmacao.value = "Preencha todos os campos antes de enviar."
            confirmacao.color = "red"
        
        page.update()

    botao_enviar = ft.Button("Enviar", on_click=enviar_formulario)

    page.add(
        ft.Column(
            [
                ft.Text("Entre em Contato", size=25, weight="bold"),
                nome,
                email,
                mensagem,
                botao_enviar,
                confirmacao
            ]
        )
    )

ft.run(main)
