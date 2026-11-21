import pytest

from objection.config import CONFIG_PADRAO
from objection.dominio.enums import FaixaConfianca
from objection.dominio.regras import calcular_probabilidade, faixa_confianca, limitar


def test_limitar():
    assert limitar(150, 0, 100) == 100
    assert limitar(-5, 0, 100) == 0
    assert limitar(40, 0, 100) == 40


def test_probabilidade_sempre_entre_5_e_95():
    assert calcular_probabilidade(50, 200, 50, 0, 0, CONFIG_PADRAO) == 95
    assert calcular_probabilidade(50, -200, 0, 50, 50, CONFIG_PADRAO) == 5


def test_probabilidade_formula():
    assert calcular_probabilidade(50, 10, 5, 4, 10, CONFIG_PADRAO) == 51


@pytest.mark.parametrize("valor,faixa", [
    (0, FaixaConfianca.HOSTIL), (24, FaixaConfianca.HOSTIL),
    (25, FaixaConfianca.DESCONFIADO), (49, FaixaConfianca.DESCONFIADO),
    (50, FaixaConfianca.RECEPTIVO), (74, FaixaConfianca.RECEPTIVO),
    (75, FaixaConfianca.CONVENCIDO), (100, FaixaConfianca.CONVENCIDO),
])
def test_faixas_de_confianca(valor, faixa):
    assert faixa_confianca(valor) is faixa
