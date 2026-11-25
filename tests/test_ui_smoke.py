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
    app.cadastrar("ana", "Senha@123")
    app.sair()
    with pytest.raises(CredenciaisInvalidasException):
        app.entrar("ana", "errada")


def test_fluxo_completo_de_uma_partida(app, pagina):
    app.cadastrar("ana", "Senha@123")
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
    app.cadastrar("ana", "Senha@123")
    app.iniciar_partida("caso-1", "cinico")
    app.usar_opcao("i-catraca")
    id_partida = app.ctrl.partida.id
    app.mostrar_home()
    app.continuar_partida(id_partida)
    assert app.ctrl.partida.orcamento == 80
    app.ir_ao_julgamento()
    app.mostrar_partida()


def test_partida_chega_a_deliberacao_e_pede_veredito(app):
    app.cadastrar("ana", "Senha@123")
    app.iniciar_partida("caso-1", "pragmatico")
    app.ir_ao_julgamento()
    for acao in ("ar-saida", "ar-chave", "ar-corredor", "ar-oficio", "ar-carater"):
        app.usar_opcao(acao)
    app.mostrar_partida()
    app.encerrar()


def test_veterano_usa_blefe_e_suborno(app):
    app.cadastrar("ana", "Senha@123")
    for i in range(3):
        app.usuario.registrar_partida_concluida(f"x{i}", True)
    app.iniciar_partida("caso-1", "cinico")
    app.usar_opcao("su-discreto")
    app.usar_opcao("al-casa")
    app.ir_ao_julgamento()
    app.usar_opcao("bl-casa")


def test_painel_do_administrador_monta(app, pagina):
    app.sessao.auth.cadastrar_administrador("chefe", "Senha@123")
    app.entrar("chefe", "Senha@123")
    assert pagina.controls


# ------------------------------------------------ Etapa 4: diálogos e painel
def _campos(dialogo):
    return dialogo.content.content.controls


def _preencher(dialogo, rotulo, valor):
    for c in _campos(dialogo):
        if getattr(c, "label", None) == rotulo:
            c.value = valor
            return
    raise AssertionError(f"campo '{rotulo}' não encontrado")


def _mensagem(dialogo):
    return _campos(dialogo)[-1].value


def _clicar(dialogo, indice=-1):
    dialogo.actions[indice].on_click(None)


@pytest.fixture
def jogando(app):
    app.cadastrar("ana", "Senha@123")
    app.iniciar_partida("caso-1", "formalista")
    return app


def test_renomear_partida_pela_tela(jogando, pagina):
    p = jogando.ctrl.partida
    jogando.mostrar_home()
    jogando.renomear_partida(p)
    dialogo = pagina.dialogos[-1]
    _preencher(dialogo, "Novo nome", "Meu caso favorito")
    _clicar(dialogo)
    assert jogando.sessao.repos.partidas.buscar_por_id(p.id).nome == "Meu caso favorito"
    assert not pagina.dialogos


def test_nome_invalido_mantem_o_dialogo_aberto_com_a_mensagem(jogando, pagina):
    p = jogando.ctrl.partida
    jogando.renomear_partida(p)
    dialogo = pagina.dialogos[-1]
    _preencher(dialogo, "Novo nome", "ab")
    _clicar(dialogo)
    assert pagina.dialogos and "3 a 60" in _mensagem(dialogo)


def test_excluir_partida_pela_tela(jogando, pagina):
    p = jogando.ctrl.partida
    jogando.mostrar_home()
    jogando.excluir_partida(p)
    _clicar(pagina.dialogos[-1])
    assert jogando.sessao.repos.partidas.buscar_por_id(p.id) is None


def test_caderno_criar_editar_excluir_pela_tela(jogando, pagina):
    jogando.usar_opcao("i-catraca")
    jogando.dialogo_anotacao()
    d = pagina.dialogos[-1]
    _preencher(d, "Título", "Saída às 17h42")
    _preencher(d, "Anotação", "A catraca confirma a saída.")
    caixas = [c for c in _campos(d) if hasattr(c, "value") and isinstance(c.value, bool)]
    assert len(caixas) == 1  # só a prova já descoberta aparece
    caixas[0].value = True
    _clicar(d)
    notas = jogando.sessao.caderno.listar(jogando.usuario, jogando.ctrl.partida.id)
    assert [(a.titulo, a.evidencias) for a in notas] == [("Saída às 17h42", ("E1",))]
    jogando.mostrar_partida()
    jogando.dialogo_anotacao(notas[0])
    d = pagina.dialogos[-1]
    _preencher(d, "Título", "Saída confirmada")
    _clicar(d)
    assert jogando.sessao.caderno.listar(jogando.usuario, jogando.ctrl.partida.id)[0].titulo == "Saída confirmada"
    jogando.excluir_anotacao(notas[0])
    _clicar(pagina.dialogos[-1])
    assert jogando.sessao.caderno.listar(jogando.usuario, jogando.ctrl.partida.id) == []


def test_anotacao_sem_titulo_mostra_erro_no_dialogo(jogando, pagina):
    jogando.dialogo_anotacao()
    d = pagina.dialogos[-1]
    _clicar(d)
    assert pagina.dialogos and "título" in _mensagem(d).lower()


@pytest.fixture
def painel(app):
    from objection.app.painel_admin import linhas_de_contas
    app.sessao.auth.cadastrar_administrador("chefe", "Senha@123")
    jogador = app.sessao.auth.cadastrar_jogador("ana", "Senha@123")
    app.entrar("chefe", "Senha@123")
    return app, jogador, lambda: linhas_de_contas(app.sessao, app.usuario)[0]


def test_todas_as_secoes_do_painel_montam(painel):
    app, _, _ = painel
    from objection.ui.admin import SECOES, _trocar
    for id_, _ in SECOES:
        _trocar(app, id_)
        assert app.secao_admin == id_


def test_admin_altera_cotas_e_concede_tokens(painel, pagina):
    from objection.ui.admin import _dialogo_cotas
    app, jogador, linha = painel
    _dialogo_cotas(app, linha())
    d = pagina.dialogos[-1]
    _preencher(d, "Cota diária (tokens)", "10000")
    _preencher(d, "Conceder tokens (opcional)", "500")
    _clicar(d)
    c = app.sessao.tokens.carteira_atual(jogador.id)
    assert c.cota_diaria == 10000 and c.saldo == 8000 + 500


def test_admin_cota_invalida_mostra_erro(painel, pagina):
    from objection.ui.admin import _dialogo_cotas
    app, _, linha = painel
    _dialogo_cotas(app, linha())
    d = pagina.dialogos[-1]
    _preencher(d, "Cota diária (tokens)", "muitos")
    _clicar(d)
    assert pagina.dialogos and "número inteiro" in _mensagem(d)


def test_admin_suspende_reativa_e_remove_conta(painel, pagina):
    from objection.ui.admin import _alternar_suspensao, _remover_conta
    app, jogador, linha = painel
    _alternar_suspensao(app, linha(), False)
    assert app.sessao.auth.consultar(jogador.id).status.value == "suspensa"
    _alternar_suspensao(app, linha(), True)
    assert app.sessao.auth.consultar(jogador.id).status.value == "ativa"
    _remover_conta(app, linha())
    _clicar(pagina.dialogos[-1])
    assert app.sessao.auth.consultar(jogador.id) is None


def test_admin_cria_edita_e_remove_pacote(painel, pagina):
    from objection.ui.admin import _dialogo_pacote, _remover_pacote
    app, _, _ = painel
    _dialogo_pacote(app)
    d = pagina.dialogos[-1]
    _preencher(d, "Nome", "Pacote de Natal")
    _preencher(d, "Tokens concedidos", "3000")
    _preencher(d, "Limite de resgates por conta (vazio = sem limite)", "2")
    _preencher(d, "Válido até, AAAA-MM-DD (vazio = sem validade)", "2026-12-31")
    _clicar(d)
    novo = [p for p in app.sessao.administracao.listar_pacotes(app.usuario) if p.nome == "Pacote de Natal"][0]
    assert (novo.tokens, novo.limite_por_conta, novo.validade_ate.isoformat()) == (3000, 2, "2026-12-31")
    _dialogo_pacote(app, novo)
    d = pagina.dialogos[-1]
    _preencher(d, "Tokens concedidos", "3500")
    _preencher(d, "Limite de resgates por conta (vazio = sem limite)", "")
    _clicar(d)
    editado = app.sessao.repos.pacotes.buscar_por_id(novo.id)
    assert editado.tokens == 3500 and editado.limite_por_conta is None
    _remover_pacote(app, editado)
    _clicar(pagina.dialogos[-1])
    assert app.sessao.repos.pacotes.buscar_por_id(novo.id) is None


def test_pacote_com_data_invalida_mostra_erro(painel, pagina):
    from objection.ui.admin import _dialogo_pacote
    app, _, _ = painel
    _dialogo_pacote(app)
    d = pagina.dialogos[-1]
    _preencher(d, "Nome", "Teste")
    _preencher(d, "Tokens concedidos", "100")
    _preencher(d, "Válido até, AAAA-MM-DD (vazio = sem validade)", "31/12/2026")
    _clicar(d)
    assert pagina.dialogos and "AAAA-MM-DD" in _mensagem(d)
