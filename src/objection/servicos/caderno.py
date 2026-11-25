import uuid
from datetime import datetime

from objection.dominio.anotacao import Anotacao
from objection.dominio.enums import Permissao
from objection.excecoes import (
    AcessoNegadoException,
    DadosInvalidosException,
    RequisitoNaoAtendidoException,
)


class ServicoCaderno:
    """CRUD das anotações do jogador em cada partida."""

    def __init__(self, repos, relogio=datetime.now):
        self._repos = repos
        self._relogio = relogio

    def _partida_do_jogador(self, usuario, id_partida):
        partida = self._repos.partidas.buscar_por_id(id_partida)
        if partida is None or partida.id_jogador != usuario.id:
            raise DadosInvalidosException("Partida não encontrada.")
        return partida

    @staticmethod
    def _checar_provas(partida, evidencias):
        """RN14: só se pode citar prova já descoberta na partida."""
        if not set(evidencias) <= partida.evidencias_descobertas:
            raise RequisitoNaoAtendidoException("Só é possível citar provas já descobertas nesta partida.")

    def _anotacao_do_jogador(self, usuario, id_anotacao):
        a = self._repos.anotacoes.buscar_por_id(id_anotacao)
        if a is None:
            raise DadosInvalidosException("Anotação não encontrada.")
        if a.id_jogador != usuario.id:
            raise AcessoNegadoException("Esta anotação pertence a outro jogador.")
        return a

    def _autorizar(self, usuario):
        usuario.exigir_ativa()
        usuario.exigir(Permissao.USAR_CADERNO)

    def criar(self, usuario, id_partida, titulo, texto="", evidencias=()) -> Anotacao:
        self._autorizar(usuario)
        partida = self._partida_do_jogador(usuario, id_partida)
        self._checar_provas(partida, evidencias)
        agora = self._relogio()
        anotacao = Anotacao(uuid.uuid4().hex[:10], partida.id, usuario.id, titulo, texto, evidencias, agora)
        self._repos.anotacoes.salvar(anotacao)
        return anotacao

    def listar(self, usuario, id_partida) -> list:
        self._autorizar(usuario)
        self._partida_do_jogador(usuario, id_partida)
        return sorted((a for a in self._repos.anotacoes.listar() if a.id_partida == id_partida),
                      key=lambda a: a.criada_em)

    def editar(self, usuario, id_anotacao, titulo=None, texto=None, evidencias=None) -> Anotacao:
        self._autorizar(usuario)
        anotacao = self._anotacao_do_jogador(usuario, id_anotacao)
        if evidencias is not None:
            self._checar_provas(self._partida_do_jogador(usuario, anotacao.id_partida), evidencias)
        anotacao.editar(self._relogio(), titulo, texto, evidencias)
        self._repos.anotacoes.salvar(anotacao)
        return anotacao

    def excluir(self, usuario, id_anotacao) -> bool:
        self._autorizar(usuario)
        anotacao = self._anotacao_do_jogador(usuario, id_anotacao)
        return self._repos.anotacoes.remover(anotacao.id)
