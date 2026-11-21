import pytest

from objection.config import ConfigBalanceamento
from objection.dominio.acao import Argumento, Blefe, Investigacao
from objection.dominio.enums import FasePartida, ResultadoVeredito
from objection.dominio.juiz import JuizCinico, JuizFormalista, JuizPragmatico
from objection.excecoes import PartidaEncerradaException, TransicaoInvalidaException
from objection.game.motor_jogo import MotorJogo


def jogar(caso, juiz, semente):
    motor = MotorJogo(semente=semente)
    p = motor.iniciar_partida(caso, "P")
    motor.executar_acao(p, caso, juiz, Investigacao("i1", "Investigar", "E1"))
    motor.iniciar_julgamento(p)
    motor.executar_acao(p, caso, juiz, Argumento("a1", "Saí cedo", ["saiu_cedo"], ["E1"]))
    motor.executar_acao(p, caso, juiz, Blefe("b1", "Outra pessoa agiu", ["outra_pessoa"], nivel=2))
    v = motor.emitir_veredito(p, caso)
    return p, v


def test_mesma_semente_gera_o_mesmo_resultado(caso):
    p1, v1 = jogar(caso, JuizCinico(), 7)
    p2, v2 = jogar(caso, JuizCinico(), 7)
    assert [e.sucesso for e in p1.historico] == [e.sucesso for e in p2.historico]
    assert (v1.resultado, v1.confianca_final, v1.suspeita_final) == \
           (v2.resultado, v2.confianca_final, v2.suspeita_final)


def test_resultado_explica_por_que_teve_sucesso_ou_falhou(caso):
    p, _ = jogar(caso, JuizFormalista(), 3)
    for evento in p.historico:
        assert evento.motivos


def test_veredito_so_depois_do_julgamento(motor, caso, partida):
    with pytest.raises(TransicaoInvalidaException):
        motor.emitir_veredito(partida, caso)
    assert partida.fase is FasePartida.PREPARACAO


def test_veredito_favoravel_e_desfavoravel_pelas_regras_do_motor(motor, caso):
    ganha = motor.iniciar_partida(caso, "G")
    ganha.ajustar_confianca(60)  # 30 + 60 = 90 (>= 60); suspeita 10 (< 50)
    motor.iniciar_julgamento(ganha)
    assert motor.emitir_veredito(ganha, caso).resultado is ResultadoVeredito.FAVORAVEL

    perde = motor.iniciar_partida(caso, "L")
    motor.iniciar_julgamento(perde)  # confiança 30 (< 60)
    assert motor.emitir_veredito(perde, caso).resultado is ResultadoVeredito.DESFAVORAVEL

    suspeito = motor.iniciar_partida(caso, "S")
    suspeito.ajustar_confianca(70)
    suspeito.ajustar_suspeita(60)  # suspeita >= 50 derruba mesmo com confiança alta
    motor.iniciar_julgamento(suspeito)
    assert motor.emitir_veredito(suspeito, caso).resultado is ResultadoVeredito.DESFAVORAVEL


def test_numero_maximo_de_rodadas_leva_a_deliberacao(caso):
    motor = MotorJogo(ConfigBalanceamento(max_rodadas=2), semente=1)
    p = motor.iniciar_partida(caso, "P")
    motor.iniciar_julgamento(p)
    j = JuizPragmatico()
    motor.executar_acao(p, caso, j, Argumento("a1", "x", ["saiu_cedo"]))
    assert p.fase is FasePartida.JULGAMENTO
    motor.executar_acao(p, caso, j, Argumento("a2", "y", ["outra_pessoa"]))
    assert p.fase is FasePartida.DELIBERACAO


def test_suspeita_maxima_encerra_o_julgamento(motor, caso, partida):
    partida.ajustar_suspeita(100)
    motor.iniciar_julgamento(partida)
    motor.executar_acao(partida, caso, JuizFormalista(), Argumento("a1", "x", ["saiu_cedo"]))
    assert partida.fase is FasePartida.DELIBERACAO
    assert motor.emitir_veredito(partida, caso).resultado is ResultadoVeredito.DESFAVORAVEL


def test_partida_encerrada_recusa_novas_acoes(motor, caso, partida):
    motor.iniciar_julgamento(partida)
    motor.emitir_veredito(partida, caso)
    with pytest.raises(PartidaEncerradaException):
        motor.executar_acao(partida, caso, JuizFormalista(), Argumento("a1", "x", ["saiu_cedo"]))
