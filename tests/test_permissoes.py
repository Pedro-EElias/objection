import pytest

from objection.dominio.acao import Argumento, Blefe, TentativaSuborno
from objection.dominio.juiz import JuizFormalista
from objection.dominio.usuario import Administrador, Jogador
from objection.excecoes import AcessoNegadoException, ContaSuspensaException


def veterano():
    j = Jogador.novo("v1", "vet", "Senha@123")
    for i in range(3):
        j.registrar_partida_concluida(f"p{i}", True)
    return j


def test_novato_nao_executa_blefe_nem_suborno_e_o_estado_nao_muda(motor, caso):
    novato = Jogador.novo("n1", "novato", "Senha@123")
    p = motor.iniciar_partida(caso, "P1", novato)
    assert p.id_jogador == "n1"
    motor.iniciar_julgamento(p)
    antes = (p.confianca, p.suspeita, p.rodada, p.versao)
    with pytest.raises(AcessoNegadoException):
        motor.executar_acao(p, caso, JuizFormalista(), Blefe("b1", "x", ["saiu_cedo"]), novato)
    assert (p.confianca, p.suspeita, p.rodada, p.versao) == antes
    motor.executar_acao(p, caso, JuizFormalista(), Argumento("a1", "x", ["saiu_cedo"]), novato)


def test_novato_nao_tenta_suborno(motor, caso):
    novato = Jogador.novo("n1", "novato", "Senha@123")
    p = motor.iniciar_partida(caso, "P1", novato)
    with pytest.raises(AcessoNegadoException):
        motor.executar_acao(p, caso, JuizFormalista(), TentativaSuborno("s1", "x"), novato)
    assert p.orcamento == 100


def test_veterano_executa_blefe(motor, caso):
    v = veterano()
    p = motor.iniciar_partida(caso, "P1", v)
    motor.iniciar_julgamento(p)
    motor.executar_acao(p, caso, JuizFormalista(), Blefe("b1", "x", ["saiu_cedo"]), v)
    assert p.rodada == 1


def test_conta_suspensa_nao_inicia_partida(motor, caso):
    j = Jogador.novo("j1", "ana", "Senha@123")
    j.suspender()
    with pytest.raises(ContaSuspensaException):
        motor.iniciar_partida(caso, "P1", j)


def test_administrador_nao_joga(motor, caso):
    a = Administrador.novo("a1", "chefe", "Senha@123")
    with pytest.raises(AcessoNegadoException):
        motor.iniciar_partida(caso, "P1", a)
