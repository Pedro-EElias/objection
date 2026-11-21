import pytest

from objection.dominio.enums import Classificacao, TipoAlegacao
from objection.dominio.juiz import Juiz, JuizCinico, JuizFormalista, JuizPragmatico
from objection.dominio.resultado import AnaliseAlegacao


def analise(tipo=TipoAlegacao.ARGUMENTO, classe=Classificacao.COERENTE, sust=2, contra=0,
            testemunhas=0, alibi=False, nivel=0):
    return AnaliseAlegacao(tipo, classe, sust, contra, 0, testemunhas, alibi, nivel)


def test_juiz_e_abstrato():
    with pytest.raises(TypeError):
        Juiz("a", "b", "c", "d")


def test_juizes_avaliam_a_mesma_alegacao_de_formas_distintas():
    a = analise(sust=2, testemunhas=2)
    notas = {type(j).__name__: j.avaliar(a).modificador
             for j in (JuizFormalista(), JuizPragmatico(), JuizCinico())}
    assert len(set(notas.values())) == 3


def test_formalista_pesa_mais_a_evidencia_que_a_pragmatica():
    a = analise(sust=3)
    assert JuizFormalista().avaliar(a).modificador > JuizPragmatico().avaliar(a).modificador


def test_pragmatica_valoriza_testemunhas():
    sem = JuizPragmatico().avaliar(analise(testemunhas=0)).modificador
    com = JuizPragmatico().avaliar(analise(testemunhas=2)).modificador
    assert com > sem


def test_pragmatica_limita_o_bonus_tecnico():
    a = JuizPragmatico().avaliar(analise(sust=3)).modificador
    b = JuizPragmatico().avaliar(analise(sust=10)).modificador
    assert a == b


def test_formalista_aumenta_suspeita_na_contradicao():
    aval = JuizFormalista().avaliar(analise(classe=Classificacao.CONTRADITORIO, contra=1))
    assert aval.multiplicador_suspeita > 1.0


def test_cinico_tolera_blefe_coerente_e_pune_blefe_fragil():
    j = JuizCinico()
    bom = j.avaliar(analise(TipoAlegacao.BLEFE, Classificacao.COERENTE, nivel=2))
    ruim = j.avaliar(analise(TipoAlegacao.BLEFE, Classificacao.FRACO, sust=0, nivel=2))
    assert bom.modificador > 0 > ruim.modificador


def test_cinico_reage_pior_a_blefe_contraditorio():
    j = JuizCinico()
    aval = j.avaliar(analise(TipoAlegacao.BLEFE, Classificacao.CONTRADITORIO, sust=0, contra=1, nivel=2))
    assert aval.multiplicador_suspeita == 2.0
