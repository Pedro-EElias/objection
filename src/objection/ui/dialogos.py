import flet as ft

from objection.excecoes import ObjectionException
from objection.ui import tema
from objection.ui.tema import botao, texto


def campo(rotulo, valor="", **extra) -> ft.TextField:
    """Campo de texto para formulários sobre papel."""
    return ft.TextField(
        label=rotulo, value=valor, color=tema.TINTA, border_color=tema.TINTA,
        focused_border_color=tema.VINHO, cursor_color=tema.TINTA,
        label_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo"),
        text_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo", size=17), **extra)


def interruptor(rotulo, valor=False) -> ft.Switch:
    return ft.Switch(label=rotulo, value=valor, active_color=tema.VINHO,
                     label_text_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo", size=16))


def caixa(rotulo, valor=False) -> ft.Checkbox:
    return ft.Checkbox(label=rotulo, value=valor, active_color=tema.VINHO,
                       label_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo", size=15))


def dialogo_formulario(app, titulo, campos, ao_salvar, ao_concluir=None, rotulo="Salvar", largura=480):
    """Abre um formulário. Erros do jogo aparecem dentro do próprio diálogo, sem fechá-lo."""
    mensagem = texto("", 15, tema.VINHO_VIVO, "CorpoMedio")

    def salvar(e=None):
        try:
            ao_salvar()
        except ObjectionException as erro:
            mensagem.value = str(erro)
            app.page.update()
            return
        app.page.pop_dialog()
        if ao_concluir:
            ao_concluir()

    app.page.show_dialog(ft.AlertDialog(
        bgcolor=tema.PAPEL, title=texto(titulo, 26, tema.TINTA, "Fell"),
        content=ft.Container(ft.Column([*campos, mensagem], spacing=12, tight=True,
                                       scroll=ft.ScrollMode.AUTO), width=largura),
        actions=[botao("Cancelar", lambda e: app.page.pop_dialog(), "secundario"),
                 botao(rotulo, salvar)]))


def dialogo_confirmacao(app, titulo, mensagem, ao_confirmar, rotulo="Confirmar"):
    def confirmar(e=None):
        app.page.pop_dialog()
        try:
            ao_confirmar()
        except ObjectionException as erro:
            app._aviso(str(erro), erro=True)

    app.page.show_dialog(ft.AlertDialog(
        bgcolor=tema.PAPEL, title=texto(titulo, 26, tema.TINTA, "Fell"),
        content=ft.Container(texto(mensagem, 17, tema.TINTA), width=440),
        actions=[botao("Cancelar", lambda e: app.page.pop_dialog(), "secundario"),
                 botao(rotulo, confirmar, "perigo")]))
