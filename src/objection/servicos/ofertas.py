import uuid
from datetime import datetime

from objection.dominio.enums import Permissao
from objection.dominio.tokens import PacoteTokens, ResgateOferta
from objection.excecoes import OfertaIndisponivelException


def pacotes_padrao() -> list:
    """Os 3 pacotes simulados do jogo. Valores provisórios."""
    return [
        PacoteTokens("boas-vindas", "Pacote de boas-vindas", 4000, limite_por_conta=1),
        PacoteTokens("diaria", "Recompensa diária", 2000, uma_por_dia=True),
        PacoteTokens("promocional", "Pacote promocional", 5000, limite_por_conta=3),
    ]


def garantir_pacotes_padrao(repos):
    """Cria os pacotes padrão só se ainda não existir nenhum."""
    if not repos.pacotes.listar():
        for p in pacotes_padrao():
            repos.pacotes.salvar(p)


class ServicoOfertas:
    """Ofertas simuladas (sem dinheiro real) que dão tokens extras ao jogador."""

    def __init__(self, repos, servico_tokens, relogio=datetime.now):
        self._repos = repos
        self._tokens = servico_tokens
        self._relogio = relogio

    def listar_disponiveis(self, jogador) -> list:
        hoje = self._relogio().date()
        return [p for p in self._repos.pacotes.listar()
                if p.esta_disponivel(hoje) and self._motivo_indisponivel(jogador, p, hoje) is None]

    def _motivo_indisponivel(self, jogador, pacote, hoje):
        resgates = [r for r in self._repos.resgates.listar()
                    if r.id_conta == jogador.id and r.id_pacote == pacote.id]
        if pacote.limite_por_conta is not None and len(resgates) >= pacote.limite_por_conta:
            return "limite de resgates atingido"
        if pacote.uma_por_dia and any(r.data == hoje for r in resgates):
            return "já resgatado hoje"
        return None

    def resgatar(self, jogador, id_pacote) -> ResgateOferta:
        jogador.exigir_ativa()
        jogador.exigir(Permissao.RESGATAR_OFERTAS)
        pacote = self._repos.pacotes.buscar_por_id(id_pacote)
        hoje = self._relogio().date()
        if pacote is None or not pacote.esta_disponivel(hoje):
            raise OfertaIndisponivelException("Esta oferta não está disponível.")
        motivo = self._motivo_indisponivel(jogador, pacote, hoje)
        if motivo:
            raise OfertaIndisponivelException(f"Oferta indisponível: {motivo}.")
        carteira = self._tokens.carteira_atual(jogador.id)
        carteira.creditar(pacote.tokens)
        self._repos.carteiras.salvar(carteira)
        resgate = ResgateOferta(uuid.uuid4().hex[:12], jogador.id, pacote.id, hoje, pacote.tokens)
        self._repos.resgates.salvar(resgate)
        return resgate
