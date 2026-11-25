import pytest

from objection.app.controlador import ControladorPartida, SessaoApp
from objection.excecoes import (
    AcessoNegadoException, ContaSuspensaException, DadosInvalidosException,
    RequisitoNaoAtendidoException,
)


@pytest.fixture
def sessao(tmp_path, relogio):
    return SessaoApp(tmp_path, relogio=relogio, semente=2)


@pytest.fixture
def jogador(sessao):
    return sessao.auth.cadastrar_jogador("ana", "Senha@123")


@pytest.fixture
def outra(sessao):
    return sessao.auth.cadastrar_jogador("bia", "Senha@123")


@pytest.fixture
def ctrl(sessao, jogador):
    return ControladorPartida.nova(sessao, jogador, "caso-1", "formalista")


# ------------------------------------------------------------------ caderno
def test_criar_e_listar_anotacoes_em_ordem(sessao, jogador, ctrl, relogio):
    sessao.caderno.criar(jogador, ctrl.partida.id, "Primeira", "texto 1")
    relogio.avancar_dias(1)
    sessao.caderno.criar(jogador, ctrl.partida.id, "Segunda")
    titulos = [a.titulo for a in sessao.caderno.listar(jogador, ctrl.partida.id)]
    assert titulos == ["Primeira", "Segunda"]


def test_anotacao_so_cita_prova_ja_descoberta(sessao, jogador, ctrl):
    with pytest.raises(RequisitoNaoAtendidoException):
        sessao.caderno.criar(jogador, ctrl.partida.id, "Teoria", "x", evidencias=["E1"])
    assert sessao.caderno.listar(jogador, ctrl.partida.id) == []
    ctrl.executar("i-catraca")
    a = sessao.caderno.criar(jogador, ctrl.partida.id, "Teoria", "x", evidencias=["E1"])
    assert a.evidencias == ("E1",)


def test_editar_anotacao(sessao, jogador, ctrl, relogio):
    a = sessao.caderno.criar(jogador, ctrl.partida.id, "Antes", "velho")
    relogio.avancar_dias(1)
    sessao.caderno.editar(jogador, a.id, titulo="Depois", texto="novo")
    atual = sessao.caderno.listar(jogador, ctrl.partida.id)[0]
    assert (atual.titulo, atual.texto) == ("Depois", "novo")
    assert atual.atualizada_em > atual.criada_em


def test_edicao_invalida_nao_altera_a_anotacao(sessao, jogador, ctrl):
    a = sessao.caderno.criar(jogador, ctrl.partida.id, "Título", "texto")
    with pytest.raises(RequisitoNaoAtendidoException):
        sessao.caderno.editar(jogador, a.id, titulo="Mudou", evidencias=["E3"])
    assert sessao.caderno.listar(jogador, ctrl.partida.id)[0].titulo == "Título"


def test_excluir_anotacao(sessao, jogador, ctrl):
    a = sessao.caderno.criar(jogador, ctrl.partida.id, "Título")
    assert sessao.caderno.excluir(jogador, a.id) is True
    assert sessao.caderno.listar(jogador, ctrl.partida.id) == []
    with pytest.raises(DadosInvalidosException):
        sessao.caderno.excluir(jogador, a.id)


def test_anotacoes_persistem_apos_reabrir(sessao, jogador, ctrl, tmp_path):
    sessao.caderno.criar(jogador, ctrl.partida.id, "Salva", "para depois")
    outra_sessao = SessaoApp(tmp_path)
    usuario = outra_sessao.repos.usuarios.buscar_por_id(jogador.id)
    assert [a.titulo for a in outra_sessao.caderno.listar(usuario, ctrl.partida.id)] == ["Salva"]


def test_validacao_de_titulo_e_texto(sessao, jogador, ctrl):
    with pytest.raises(DadosInvalidosException):
        sessao.caderno.criar(jogador, ctrl.partida.id, "   ")
    with pytest.raises(DadosInvalidosException):
        sessao.caderno.criar(jogador, ctrl.partida.id, "t" * 61)
    with pytest.raises(DadosInvalidosException):
        sessao.caderno.criar(jogador, ctrl.partida.id, "ok", "x" * 601)


def test_jogador_nao_mexe_no_caderno_de_outro(sessao, jogador, outra, ctrl):
    a = sessao.caderno.criar(jogador, ctrl.partida.id, "Minha")
    with pytest.raises(DadosInvalidosException):
        sessao.caderno.listar(outra, ctrl.partida.id)
    with pytest.raises(DadosInvalidosException):
        sessao.caderno.criar(outra, ctrl.partida.id, "Invasão")
    with pytest.raises(AcessoNegadoException):
        sessao.caderno.editar(outra, a.id, titulo="Hackeada")
    with pytest.raises(AcessoNegadoException):
        sessao.caderno.excluir(outra, a.id)


def test_administrador_nao_usa_caderno(sessao, ctrl):
    admin = sessao.auth.cadastrar_administrador("chefe", "Senha@123")
    with pytest.raises(AcessoNegadoException):
        sessao.caderno.listar(admin, ctrl.partida.id)


# ----------------------------------------------------------------- partidas
def test_renomear_partida(sessao, jogador, ctrl, tmp_path):
    sessao.partidas.renomear(jogador, ctrl.partida.id, "Meu primeiro caso")
    reaberta = SessaoApp(tmp_path)
    assert reaberta.repos.partidas.buscar_por_id(ctrl.partida.id).nome == "Meu primeiro caso"


def test_nome_de_partida_invalido(sessao, jogador, ctrl):
    for nome in ("ab", "x" * 61, "   "):
        with pytest.raises(DadosInvalidosException):
            sessao.partidas.renomear(jogador, ctrl.partida.id, nome)


def test_excluir_partida_apaga_as_anotacoes_dela(sessao, jogador, ctrl):
    sessao.caderno.criar(jogador, ctrl.partida.id, "Nota")
    sessao.partidas.excluir(jogador, ctrl.partida.id)
    assert sessao.repos.partidas.buscar_por_id(ctrl.partida.id) is None
    assert sessao.repos.anotacoes.listar() == []


def test_jogador_nao_renomeia_nem_exclui_partida_de_outro(sessao, outra, ctrl):
    with pytest.raises(DadosInvalidosException):
        sessao.partidas.renomear(outra, ctrl.partida.id, "Roubada")
    with pytest.raises(DadosInvalidosException):
        sessao.partidas.excluir(outra, ctrl.partida.id)


def test_conta_suspensa_nao_gerencia_partidas(sessao, jogador, ctrl):
    jogador.suspender()
    with pytest.raises(ContaSuspensaException):
        sessao.partidas.renomear(jogador, ctrl.partida.id, "Qualquer nome")


def test_excluir_a_propria_conta_apaga_partidas_e_anotacoes(sessao, jogador, ctrl):
    sessao.caderno.criar(jogador, ctrl.partida.id, "Nota")
    sessao.auth.excluir_conta(jogador, "Senha@123")
    assert sessao.repos.partidas.listar() == [] and sessao.repos.anotacoes.listar() == []


def test_admin_remove_conta_e_apaga_os_dados_do_jogador(sessao, jogador, ctrl):
    admin = sessao.auth.cadastrar_administrador("chefe", "Senha@123")
    sessao.caderno.criar(jogador, ctrl.partida.id, "Nota")
    sessao.administracao.remover_conta(admin, jogador.id)
    assert sessao.repos.partidas.listar() == [] and sessao.repos.anotacoes.listar() == []
