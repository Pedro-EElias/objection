"""Objetos de valor (imutáveis) trocados entre ações, juízes e motor."""
from dataclasses import dataclass
from typing import Optional

from objection.dominio.enums import (
    Classificacao,
    FaixaConfianca,
    ResultadoVeredito,
    TipoAlegacao,
)


@dataclass(frozen=True)
class AnaliseAlegacao:
    """Resumo objetivo de uma alegação, calculado pelo motor e avaliado pelo juiz."""

    tipo: TipoAlegacao
    classificacao: Optional[Classificacao]
    evidencias_sustentando: int
    contradicoes: int
    evidencias_ausentes: int
    testemunhas_preparadas: int
    alibi_preparado: bool
    nivel_risco: int


@dataclass(frozen=True)
class AvaliacaoJuiz:
    modificador: int
    multiplicador_suspeita: float
    motivos: tuple


@dataclass(frozen=True)
class ResultadoAcao:
    id_acao: str
    sucesso: bool
    delta_confianca: int = 0
    delta_suspeita: int = 0
    evidencias_reveladas: tuple = ()
    marcadores: tuple = ()
    motivos: tuple = ()
    probabilidade: Optional[int] = None
    classificacao: Optional[Classificacao] = None


@dataclass(frozen=True)
class HistoricoEvento:
    rodada: int
    id_acao: str
    descricao: str
    sucesso: bool
    delta_confianca: int
    delta_suspeita: int
    motivos: tuple


@dataclass(frozen=True)
class Veredito:
    resultado: ResultadoVeredito
    confianca_final: int
    suspeita_final: int
    faixa: FaixaConfianca
    motivos: tuple
