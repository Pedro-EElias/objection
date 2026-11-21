import pytest

from objection.dominio.enums import FasePartida
from objection.dominio.partida import Partida
from objection.excecoes import (
    DadosInvalidosException,
    ObjectionException,
    OrcamentoInsuficienteException,
    PartidaEncerradaException,
    TransicaoInvalidaException,
)
import objection.excecoes as exc


def test_confianca_e_suspeita_ficam_entre_0_e_100(partida):
    partida.ajustar_confianca(500)
    partida.ajustar_suspeita(500)
    assert (partida.confianca, partida.suspeita) == (100, 100)
    partida.ajustar_confianca(-500)
    partida.ajustar_suspeita(-500)
    assert (partida.confianca, partida.suspeita) == (0, 0)


def test_orcamento_nunca_fica_negativo(partida):
    antes = partida.orcamento
    with pytest.raises(OrcamentoInsuficienteException):
        partida.debitar(antes + 1)
    assert partida.orcamento == antes


def test_debito_negativo_e_rejeitado(partida):
    with pytest.raises(DadosInvalidosException):
        partida.debitar(-1)


def test_estado_inicial_invalido_e_rejeitado():
    with pytest.raises(DadosInvalidosException):
        Partida("P", "C", -1, 30, 10)
    with pytest.raises(DadosInvalidosException):
        Partida("P", "C", 100, 101, 10)


def test_transicoes_validas(partida):
    partida.mudar_fase(FasePartida.JULGAMENTO)
    partida.mudar_fase(FasePartida.DELIBERACAO)
    partida.mudar_fase(FasePartida.ENCERRADA)
    assert partida.encerrada


def test_nao_pula_preparacao_para_deliberacao(partida):
    with pytest.raises(TransicaoInvalidaException):
        partida.mudar_fase(FasePartida.DELIBERACAO)
    assert partida.fase is FasePartida.PREPARACAO


def test_partida_encerrada_nao_aceita_acoes(partida):
    partida.mudar_fase(FasePartida.ABANDONADA)
    with pytest.raises(PartidaEncerradaException):
        partida.garantir_ativa()
    with pytest.raises(TransicaoInvalidaException):
        partida.mudar_fase(FasePartida.JULGAMENTO)


def test_versao_aumenta_a_cada_alteracao(partida):
    v = partida.versao
    partida.ajustar_confianca(1)
    assert partida.versao == v + 1


def test_todas_as_excecoes_herdam_da_raiz():
    for nome in dir(exc):
        obj = getattr(exc, nome)
        if isinstance(obj, type) and nome.endswith("Exception") and obj is not ObjectionException:
            assert issubclass(obj, ObjectionException), nome
