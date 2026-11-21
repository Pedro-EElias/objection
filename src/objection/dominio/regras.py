"""Funções puras de regra, fáceis de testar."""
from objection.config import ConfigBalanceamento
from objection.dominio.enums import FaixaConfianca


def limitar(valor: int, minimo: int, maximo: int) -> int:
    return max(minimo, min(maximo, valor))


def calcular_probabilidade(
    base: int,
    modificador_juiz: int,
    bonus_contexto: int,
    penalidade_suspeita: int,
    risco: int,
    config: ConfigBalanceamento,
) -> int:
    """probabilidade = limitar(base + juiz + contexto - suspeita - risco, min, max)"""
    bruto = base + modificador_juiz + bonus_contexto - penalidade_suspeita - risco
    return limitar(bruto, config.prob_min, config.prob_max)


def faixa_confianca(confianca: int) -> FaixaConfianca:
    if confianca < 25:
        return FaixaConfianca.HOSTIL
    if confianca < 50:
        return FaixaConfianca.DESCONFIADO
    if confianca < 75:
        return FaixaConfianca.RECEPTIVO
    return FaixaConfianca.CONVENCIDO
