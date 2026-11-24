"""Parâmetros de balanceamento centralizados. Ajustar aqui, nunca espalhar números pelo código."""
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
    prob_base: int = 60
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
    ganho_argumento: int = 8
    ganho_por_evidencia: int = 10
    perda_argumento: int = 3
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
    # Progressão do jogador (RN12)
    partidas_para_promocao: int = 3
    vitorias_para_promocao: int = 2
    # Energia de IA (valores provisórios: medir o consumo real e ajustar)
    cota_diaria_padrao: int = 8000
    cota_por_caso_padrao: int = 6000


CONFIG_PADRAO = ConfigBalanceamento()
