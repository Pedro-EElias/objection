import uuid
from datetime import datetime

from objection.dominio.tokens import RegistroConsumo
from objection.excecoes import DadosInvalidosException, VersaoConflitanteException


class ServicoTokens:
    """Energia de IA: recarga diária, autorização antes da chamada e livro de consumo."""

    def __init__(self, repos, relogio=datetime.now):
        self._repos = repos
        self._relogio = relogio

    @staticmethod
    def estimar_tokens(texto: str) -> int:
        """Estimativa simples (~4 caracteres por token), usada no modo local/simulado."""
        return max(1, len(texto) // 4)

    def carteira_atual(self, id_conta):
        """Devolve a carteira já recarregada para o dia (com uma nova tentativa em caso de conflito)."""
        for tentativa in (1, 2):
            carteira = self._repos.carteiras.buscar_por_id(id_conta)
            if carteira is None:
                raise DadosInvalidosException("A conta não possui carteira de tokens.")
            if not carteira.recarregar_se_novo_dia(self._relogio().date()):
                return carteira
            try:
                self._repos.carteiras.salvar(carteira)
                return carteira
            except VersaoConflitanteException:
                self._repos.carteiras.recarregar()
                if tentativa == 2:
                    raise

    def energia(self, jogador) -> int:
        """Percentual que o jogador enxerga (ex.: 90 de 100)."""
        return self.carteira_atual(jogador.id).energia_percentual

    def saldo_diario(self, jogador) -> tuple:
        """Devolve (saldo atual, cota diária), em tokens."""
        carteira = self.carteira_atual(jogador.id)
        return carteira.saldo, carteira.cota_diaria

    def cota_caso(self, jogador, id_caso) -> tuple:
        """Devolve (tokens restantes, limite diário) para o caso atual."""
        carteira = self.carteira_atual(jogador.id)
        usados = carteira.consumo_por_caso.get(id_caso, 0)
        return max(0, carteira.cota_por_caso - usados), carteira.cota_por_caso

    def autorizar_chamada(self, jogador, id_caso, estimativa):
        """RN16: levanta exceção se faltar saldo ou cota do caso; o jogo segue no modo offline."""
        jogador.exigir_ativa()
        self.carteira_atual(jogador.id).autorizar(estimativa, id_caso)

    def registrar_consumo(self, jogador, id_caso, id_juiz, provedor,
                          tokens_entrada, tokens_saida, simulado=False, debitar=None) -> RegistroConsumo:
        """RN17: todo consumo vai para o livro, inclusive o simulado.

        Só o consumo real desconta energia (a energia vale só para o modo online). Passe
        debitar=True para forçar o desconto, por exemplo numa demonstração.
        """
        debitar = (not simulado) if debitar is None else debitar
        registro = RegistroConsumo(
            uuid.uuid4().hex[:12], jogador.id, id_caso, id_juiz, provedor,
            tokens_entrada, tokens_saida, simulado, self._relogio())
        if debitar:
            for tentativa in (1, 2):
                try:
                    carteira = self.carteira_atual(jogador.id)
                    carteira.consumir(registro.total, id_caso)
                    self._repos.carteiras.salvar(carteira)
                    break
                except VersaoConflitanteException:
                    self._repos.carteiras.recarregar()
                    if tentativa == 2:
                        raise
        self._repos.consumos.salvar(registro)
        return registro
