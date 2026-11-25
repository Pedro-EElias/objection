from objection.excecoes import DadosInvalidosException


def limpar_dados_do_jogador(repos, id_jogador) -> int:
    """Apaga partidas e anotações de um jogador (usado ao excluir a conta). Devolve quantas partidas."""
    partidas = [p for p in repos.partidas.listar() if p.id_jogador == id_jogador]
    for p in partidas:
        _apagar_partida(repos, p.id)
    return len(partidas)


def _apagar_partida(repos, id_partida):
    for a in [a for a in repos.anotacoes.listar() if a.id_partida == id_partida]:
        repos.anotacoes.remover(a.id)
    repos.partidas.remover(id_partida)


class ServicoPartidas:
    """Gerenciamento das partidas salvas do jogador (consultar, renomear, excluir)."""

    def __init__(self, repos):
        self._repos = repos

    def _da_pessoa(self, usuario, id_partida):
        partida = self._repos.partidas.buscar_por_id(id_partida)
        if partida is None or partida.id_jogador != usuario.id:
            raise DadosInvalidosException("Partida não encontrada.")
        return partida

    def listar(self, usuario) -> list:
        return [p for p in self._repos.partidas.listar() if p.id_jogador == usuario.id]

    def renomear(self, usuario, id_partida, novo_nome):
        usuario.exigir_ativa()
        partida = self._da_pessoa(usuario, id_partida)
        partida.renomear(novo_nome)
        self._repos.partidas.salvar(partida)
        return partida

    def excluir(self, usuario, id_partida):
        """Exclui a partida e as anotações dela."""
        usuario.exigir_ativa()
        partida = self._da_pessoa(usuario, id_partida)
        _apagar_partida(self._repos, partida.id)
