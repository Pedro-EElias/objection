from dataclasses import dataclass, field
from typing import Optional

from objection.dominio.enums import Classificacao

EVENTOS_OBJECAO = frozenset({"contradicao", "suborno_descoberto", "conduta_inadequada"})


@dataclass(frozen=True)
class ContextoReacao:
    """Tudo o que um provedor pode saber para o juiz falar. Só informação autorizada do caso."""

    evento: str
    indice: int = 0
    id_caso: str = ""
    texto_alegacao: str = ""
    classificacao: Optional[Classificacao] = None
    sucesso: Optional[bool] = None
    codigos_motivo: tuple = ()
    faixa_confianca: str = ""
    nivel_suspeita: str = ""
    rodada: int = 0
    fatos_publicos: tuple = ()

    def texto_resumo(self) -> str:
        return " ".join([self.texto_alegacao, *self.fatos_publicos])


@dataclass(frozen=True)
class ContextoInterpretacao:
    """Pedido para a IA dizer QUAIS afirmações do caso um argumento livre faz."""

    texto: str
    afirmacoes_possiveis: dict = field(default_factory=dict)   # etiqueta -> descrição (lista fechada)
    provas_descobertas: tuple = ()                             # (id, descrição, etiquetas que apoia)
    id_caso: str = ""
    rodada: int = 0


@dataclass(frozen=True)
class Interpretacao:
    """O que a IA entendeu. É só uma sugestão: o motor valida e calcula o efeito."""

    afirmacoes: tuple
    clareza: int
    provedor: str = ""
    tokens_entrada: int = 0
    tokens_saida: int = 0
    conduta_inadequada: bool = False
