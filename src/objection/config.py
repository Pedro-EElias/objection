"""Parâmetros de balanceamento centralizados aqui para ajuste"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigBalanceamento:
    # Estado inicial
    orcamento_inicial: int = 100
    confianca_inicial: int = 30
    suspeita_inicial: int = 10
    # Julgamento
    max_rodadas: int = 6
    suspeita_maxima: int = 100
    # Probabilidade
    prob_base: int = 50
    prob_base_suborno: int = 45
    prob_min: int = 5
    prob_max: int = 95
    divisor_penalidade_suspeita: int = 4
    bonus_contexto_por_evidencia: int = 5
    bonus_contexto_maximo: int = 15
    # Custos (créditos do caso)
    custo_investigar: int = 20
    custo_testemunha: int = 15
    custo_alibi: int = 35
    custo_suborno: int = 50
    # Efeitos
    ganho_argumento: int = 10
    ganho_por_evidencia: int = 5
    perda_argumento: int = 5
    suspeita_falha_argumento: int = 5
    ganho_blefe_base: int = 10
    ganho_blefe_por_nivel: int = 5
    perda_blefe: int = 10
    risco_blefe_por_nivel: int = 10
    suspeita_contradicao: int = 15
    ganho_suborno: int = 30
    suspeita_suborno_sucesso: int = 10
    perda_suborno: int = 30
    suspeita_suborno_descoberto: int = 40


CONFIG_PADRAO = ConfigBalanceamento()
