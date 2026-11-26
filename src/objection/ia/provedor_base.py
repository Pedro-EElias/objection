from abc import ABC, abstractmethod
from dataclasses import dataclass

from objection.excecoes import ProvedorIAIndisponivelException


@dataclass(frozen=True)
class ReacaoJuiz:
    """Fala do juiz. Texto livre: nunca altera o estado do jogo."""

    dialogo: str
    objecao: bool = False
    provedor: str = "local"
    tokens_entrada: int = 0
    tokens_saida: int = 0
    simulado: bool = True


class ProvedorIA(ABC):
    """Contrato comum para gerar a reação de um juiz (local ou IA externa)."""

    nome = "base"

    @abstractmethod
    def gerar_reacao(self, juiz, contexto) -> ReacaoJuiz:
        """Devolve a fala do juiz para o contexto. Pode levantar ProvedorIAIndisponivelException
        ou RespostaIAInvalidaException; quem chama cai no provedor local."""

    def estimar_tokens(self, juiz, contexto) -> int:
        """Estimativa do custo de uma chamada, usada para autorizar antes de gastar energia."""
        return 700

    def interpretar(self, contexto):
        """Interpreta um argumento livre (devolve Interpretacao). Só provedores de IA implementam."""
        raise ProvedorIAIndisponivelException("Este provedor não interpreta texto livre.")

    def estimar_tokens_interpretacao(self, contexto) -> int:
        return 900
