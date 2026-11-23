import pytest

from objection.dominio.enums import NivelJogador, Permissao, StatusConta
from objection.dominio.usuario import Administrador, Jogador, Usuario
from objection.excecoes import (
    AcessoNegadoException, ContaSuspensaException, DadosInvalidosException,
    TransicaoInvalidaException,
)


def novo_jogador():
    return Jogador.novo("j1", "ana", "senha123")


def test_usuario_e_abstrato():
    with pytest.raises(TypeError):
        Usuario("1", "ana", "h", "s", 1)


def test_senha_e_guardada_como_hash():
    j = novo_jogador()
    assert "senha123" not in j.senha_hash
    assert j.verificar_senha("senha123")
    assert not j.verificar_senha("outra")
    assert not j.verificar_senha(None)


def test_mesma_senha_gera_hashes_diferentes_por_causa_do_salt():
    assert Jogador.novo("a", "ana", "senha123").senha_hash != Jogador.novo("b", "bia", "senha123").senha_hash


def test_senha_curta_e_apelido_invalido_sao_rejeitados():
    with pytest.raises(DadosInvalidosException):
        Jogador.novo("j", "ana", "123")
    with pytest.raises(DadosInvalidosException):
        Jogador.novo("j", "a b", "senha123")


def test_novato_nao_tem_blefe_nem_suborno_mas_veterano_tem():
    j = novo_jogador()
    assert j.pode(Permissao.JOGAR)
    assert not j.pode(Permissao.USAR_BLEFE) and not j.pode(Permissao.USAR_SUBORNO)
    for i in range(3):
        j.registrar_partida_concluida(f"p{i}", venceu=True)
    assert j.nivel is NivelJogador.VETERANO
    assert j.pode(Permissao.USAR_BLEFE) and j.pode(Permissao.USAR_SUBORNO)


def test_administrador_gerencia_mas_nao_joga():
    a = Administrador.novo("a1", "chefe", "senha123")
    assert a.pode(Permissao.VER_CONSUMO) and a.pode(Permissao.GERENCIAR_COTAS)
    assert not a.pode(Permissao.JOGAR)
    with pytest.raises(AcessoNegadoException):
        a.exigir(Permissao.JOGAR)


def test_promocao_exige_3_partidas_e_2_vitorias():
    j = novo_jogador()
    j.registrar_partida_concluida("p1", True)
    j.registrar_partida_concluida("p2", False)
    assert j.registrar_partida_concluida("p3", False) is False
    assert j.nivel is NivelJogador.NOVATO
    assert j.registrar_partida_concluida("p4", True) is True
    assert j.nivel is NivelJogador.VETERANO


def test_partida_concluida_conta_uma_unica_vez():
    j = novo_jogador()
    assert j.registrar_partida_concluida("p1", True) is False
    j.registrar_partida_concluida("p1", True)
    j.registrar_partida_concluida("p1", True)
    assert j.vitorias == 1 and len(j.partidas_concluidas) == 1


def test_estado_da_conta():
    j = novo_jogador()
    j.suspender()
    with pytest.raises(ContaSuspensaException):
        j.exigir_ativa()
    with pytest.raises(TransicaoInvalidaException):
        j.suspender()
    j.reativar()
    j.marcar_excluida()
    assert j.status is StatusConta.EXCLUIDA
    with pytest.raises(TransicaoInvalidaException):
        j.reativar()

