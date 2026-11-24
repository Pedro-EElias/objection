"""Monta cada tela com os controles reais do Flet e simula o fluxo completo.

Não verifica a aparência (isso só se vê abrindo o jogo), mas pega erros de montagem,
argumentos inválidos de controles e falhas de ligação entre tela e controlador.
"""
from types import SimpleNamespace

import msgpack
import pytest
from flet.controls.base_control import BaseControl
from flet.messaging.protocol import configure_encode_object_for_msgpack

from objection.app.controlador import SessaoApp
from objection.dominio.enums import FasePartida
from objection.excecoes import CredenciaisInvalidasException
from objection.ui.app import AppUI


_CODIFICAR = configure_encode_object_for_msgpack(BaseControl)


def serializar(controle):
    """Codifica a árvore como o Flet faz ao enviar para a janela (pega valores inválidos)."""
    return msgpack.packb(controle, default=_CODIFICAR)


class PaginaFalsa:
    def __init__(self):
        self.window = SimpleNamespace()
        self.controls = []
        self.dialogos = []
        self.atualizacoes = 0

    def clean(self):
        self.controls = []

    def add(self, controle):
        serializar(controle)
        self.controls.append(controle)

    def update(self):
        self.atualizacoes += 1

    def show_dialog(self, dialogo):
        serializar(dialogo)
        self.dialogos.append(dialogo)

    def pop_dialog(self):
        return self.dialogos.pop() if self.dialogos else None


@pytest.fixture
def pagina():
    return PaginaFalsa()


@pytest.fixture
def app(pagina, tmp_path, relogio):
    sessao = SessaoApp(tmp_path, relogio=relogio, semente=5)
    ui = AppUI(pagina, sessao, pausa_carimbo=0)
    ui.iniciar()
    return ui


def test_tela_de_login_e_cadastro_montam(app, pagina):
    assert pagina.controls
    app.mostrar_login("cadastro")
    assert pagina.controls


def test_login_com_senha_errada(app):
    app.cadastrar("ana", "senha123")
    app.sair()
    with pytest.raises(CredenciaisInvalidasException):
        app.entrar("ana", "errada")


def test_fluxo_completo_de_uma_partida(app, pagina):
    app.cadastrar("ana", "senha123")
    assert app.usuario.apelido == "ana"
    app.mostrar_ofertas()
    assert pagina.dialogos
    app.resgatar("diaria")
    app.mostrar_intro_caso("caso-1")
    app.iniciar_partida("caso-1", "formalista")
    assert app.ctrl.fase is FasePartida.PREPARACAO
    for acao in ("i-mensagens", "i-catraca", "t-corredor"):
        app.usar_opcao(acao)
    app.usar_opcao("i-catraca")  # repetida: mostra aviso e não quebra a tela
    app.ir_ao_julgamento()
    assert app.fala
    app.usar_opcao("ar-saida")  # contradiz a mensagem descoberta: dispara a objeção
    app.usar_opcao("bl-seguranca")  # bloqueada para novato: aviso, tela continua
    app.usar_opcao("ar-carater")
    app.encerrar()
    assert app.ctrl.fase is FasePartida.ENCERRADA
    app.mostrar_home()
    assert pagina.controls


def test_continuar_partida_salva(app):
    app.cadastrar("ana", "senha123")
    app.iniciar_partida("caso-1", "cinico")
    app.usar_opcao("i-catraca")
    id_partida = app.ctrl.partida.id
    app.mostrar_home()
    app.continuar_partida(id_partida)
    assert app.ctrl.partida.orcamento == 80
    app.ir_ao_julgamento()
    app.mostrar_partida()


def test_partida_chega_a_deliberacao_e_pede_veredito(app):
    app.cadastrar("ana", "senha123")
    app.iniciar_partida("caso-1", "pragmatico")
    app.ir_ao_julgamento()
    for acao in ("ar-saida", "ar-chave", "ar-corredor", "ar-oficio", "ar-carater"):
        app.usar_opcao(acao)
    app.mostrar_partida()
    app.encerrar()


def test_veterano_usa_blefe_e_suborno(app):
    app.cadastrar("ana", "senha123")
    for i in range(3):
        app.usuario.registrar_partida_concluida(f"x{i}", True)
    app.iniciar_partida("caso-1", "cinico")
    app.usar_opcao("su-discreto")
    app.usar_opcao("al-casa")
    app.ir_ao_julgamento()
    app.usar_opcao("bl-casa")


def test_painel_do_administrador_monta(app, pagina):
    app.sessao.auth.cadastrar_administrador("chefe", "senha123")
    app.entrar("chefe", "senha123")
    assert pagina.controls
