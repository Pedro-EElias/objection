from datetime import date

import pytest

from objection.dominio.tokens import CarteiraTokens
from objection.excecoes import CotaDoCasoExcedidaException, TokensInsuficientesException


def carteira():
    return CarteiraTokens("c1", cota_diaria=1000, cota_por_caso=600)


def test_recarga_diaria_nao_acumula():
    c = carteira()
    assert c.recarregar_se_novo_dia(date(2026, 11, 20)) is True
    c.consumir(300, "caso-1")
    assert c.recarregar_se_novo_dia(date(2026, 11, 20)) is False  # mesmo dia
    assert c.saldo == 700
    c.recarregar_se_novo_dia(date(2026, 11, 21))
    assert c.saldo == 1000 and c.consumo_por_caso == {}


def test_saldo_nunca_fica_negativo():
    c = carteira()
    c.consumir(5000, "caso-1")
    assert c.saldo == 0
    c.revogar(10)
    assert c.saldo == 0


def test_autorizar_recusa_sem_saldo():
    c = carteira()
    c.consumir(950, "caso-1")
    with pytest.raises(TokensInsuficientesException):
        c.autorizar(100, "caso-2")


def test_autorizar_respeita_a_cota_por_caso():
    c = carteira()
    c.consumir(500, "caso-1")
    c.autorizar(100, "caso-1")  # 600/600 ainda cabe
    with pytest.raises(CotaDoCasoExcedidaException):
        c.autorizar(101, "caso-1")
    c.autorizar(101, "caso-2")  # outro caso tem a própria cota


def test_energia_percentual_para_o_jogador():
    c = carteira()
    assert c.energia_percentual == 100
    c.consumir(100, "caso-1")
    assert c.energia_percentual == 90
    c.creditar(5000)
    assert c.energia_percentual == 100  # nunca passa de 100
    c.revogar(10_000)
    assert c.energia_percentual == 0


def test_extras_acima_da_cota_sobrevivem_a_recarga():
    c = carteira()
    c.recarregar_se_novo_dia(date(2026, 11, 20))
    c.creditar(4000)  # oferta: 5000 no total
    c.recarregar_se_novo_dia(date(2026, 11, 21))
    assert c.saldo == 5000
