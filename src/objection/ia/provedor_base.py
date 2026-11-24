from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ReacaoJuiz:
    """Fala do juiz. Texto livre: nunca altera o estado do jogo."""

    dialogo: str
    objecao: bool = False


class ProvedorIA(ABC):
    """Contrato comum para gerar a reação de um juiz (local ou IA externa)."""

    nome = "base"

    @abstractmethod
    def gerar_reacao(self, juiz, evento: str, indice: int = 0) -> ReacaoJuiz:
        """evento: abertura, convenceu, nao_convenceu, contradicao, sem_evidencia,
        suborno_ok, suborno_descoberto, veredito_favoravel, veredito_desfavoravel."""
