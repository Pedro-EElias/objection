import pytest

from objection.dominio.acao import (
    Argumento, Blefe, Investigacao, PrepararAlibi, PrepararTestemunha, TentativaSuborno,
)
from objection.dominio.juiz import JuizFormalista
from objection.excecoes import (
    AcaoJaExecutadaException, DadosInvalidosException, EvidenciaInexistenteException,
    FaseInvalidaException, OrcamentoInsuficienteException, RequisitoNaoAtendidoException,
)


@pytest.fixture
def juiz():
    return JuizFormalista()


def snapshot(p):
    return (p.orcamento, p.confianca, p.suspeita, p.versao, p.fase,
            p.evidencias_descobertas, p.acoes_executadas, len(p.historico))


def test_investigacao_revela_evidencia_e_cobra_custo(motor, caso, partida, juiz):
    acao = Investigacao("i1", "Investigar o registro", "E1")
    motor.executar_acao(partida, caso, juiz, acao)
    assert "E1" in partida.evidencias_descobertas
    assert partida.orcamento == 100 - 20


def test_evidencia_nao_e_descoberta_duas_vezes(motor, caso, partida, juiz):
    motor.executar_acao(partida, caso, juiz, Investigacao("i1", "a", "E1"))
    with pytest.raises(AcaoJaExecutadaException):
        motor.executar_acao(partida, caso, juiz, Investigacao("i2", "b", "E1"))


def test_mesma_acao_nao_roda_duas_vezes(motor, caso, partida, juiz):
    acao = PrepararTestemunha("t1", "Preparar T1", "T1")
    motor.executar_acao(partida, caso, juiz, acao)
    with pytest.raises(AcaoJaExecutadaException):
        motor.executar_acao(partida, caso, juiz, acao)


def test_acao_invalida_nao_altera_o_estado(motor, caso, partida, juiz):
    antes = snapshot(partida)
    for acao in (Argumento("a1", "x", ["saiu_cedo"]),            # fase errada
                 Investigacao("i9", "x", "E9"),                   # evidência inexistente
                 PrepararTestemunha("t9", "x", "T9")):            # testemunha inexistente
        with pytest.raises((FaseInvalidaException, EvidenciaInexistenteException,
                            DadosInvalidosException)):
            motor.executar_acao(partida, caso, juiz, acao)
    assert snapshot(partida) == antes


def test_orcamento_insuficiente_nao_altera_o_estado(motor, caso, partida, juiz):
    partida.debitar(95)
    antes = snapshot(partida)
    with pytest.raises(OrcamentoInsuficienteException):
        motor.executar_acao(partida, caso, juiz, Investigacao("i1", "x", "E1"))
    assert snapshot(partida) == antes


def test_blefe_nivel_3_exige_alibi(motor, caso, partida, juiz):
    motor.iniciar_julgamento(partida)
    blefe = Blefe("b1", "Tenho um álibi", ["saiu_cedo"], nivel=3)
    with pytest.raises(RequisitoNaoAtendidoException):
        motor.executar_acao(partida, caso, juiz, blefe)


def test_blefe_nivel_3_liberado_com_alibi(motor, caso, partida, juiz):
    motor.executar_acao(partida, caso, juiz, PrepararAlibi("al1", "Álibi", "estava_em_casa"))
    motor.iniciar_julgamento(partida)
    motor.executar_acao(partida, caso, juiz, Blefe("b1", "Blefe alto", ["saiu_cedo"], nivel=3))
    assert partida.rodada == 1


def test_suborno_so_uma_vez_por_partida(motor, caso, partida, juiz):
    motor.executar_acao(partida, caso, juiz, TentativaSuborno("s1", "Oferta discreta"))
    with pytest.raises(AcaoJaExecutadaException):
        motor.executar_acao(partida, caso, juiz, TentativaSuborno("s2", "Outra oferta"))


def test_jogo_nunca_trava_por_falta_de_creditos(motor, caso, partida, juiz):
    """RN01 só afeta a preparação: com 0 créditos ainda dá para julgar e chegar ao veredito."""
    partida.debitar(partida.orcamento)
    with pytest.raises(OrcamentoInsuficienteException):
        motor.executar_acao(partida, caso, juiz, Investigacao("i1", "x", "E1"))
    motor.iniciar_julgamento(partida)
    motor.executar_acao(partida, caso, juiz, Argumento("a1", "Saí cedo", ["saiu_cedo"]))
    veredito = motor.emitir_veredito(partida, caso)
    assert veredito is not None and partida.encerrada


def test_argumento_sem_evidencia_descoberta_e_classificado_assim(motor, caso, partida, juiz):
    motor.iniciar_julgamento(partida)
    r = motor.executar_acao(partida, caso, juiz,
                            Argumento("a1", "Saí cedo", ["saiu_cedo"], evidencias_citadas=["E1"]))
    assert r.classificacao.value == "sem_evidencia"


def test_contradicao_com_evidencia_descoberta_e_detectada(motor, caso, partida, juiz):
    motor.executar_acao(partida, caso, juiz, Investigacao("i3", "x", "E3"))
    motor.iniciar_julgamento(partida)
    r = motor.executar_acao(partida, caso, juiz, Argumento("a1", "Saí cedo", ["saiu_cedo"]))
    assert r.classificacao.value == "contraditorio"


def test_contradicao_com_declaracao_anterior(motor, caso, partida, juiz):
    motor.iniciar_julgamento(partida)
    motor.executar_acao(partida, caso, juiz, Argumento("a1", "Saí cedo", ["saiu_cedo"]))
    r = motor.executar_acao(partida, caso, juiz, Argumento("a2", "Fiquei até tarde", ["ficou_tarde"]))
    assert r.classificacao.value == "contraditorio"
