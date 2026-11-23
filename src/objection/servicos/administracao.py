import uuid
from collections import defaultdict
from datetime import datetime

from objection.dominio.enums import Permissao
from objection.dominio.tokens import PacoteTokens
from objection.dominio.usuario import Jogador
from objection.excecoes import DadosInvalidosException


class ServicoAdministracao:
    """Operações do perfil Administrador. Toda operação confere a permissão primeiro."""

    def __init__(self, repos, servico_tokens, relogio=datetime.now):
        self._repos = repos
        self._tokens = servico_tokens
        self._relogio = relogio

    # --- consulta ---
    def listar_contas(self, admin) -> list:
        admin.exigir_ativa()
        admin.exigir(Permissao.GERENCIAR_CONTAS)
        return self._repos.usuarios.listar()

    def resumo_consumo(self, admin) -> dict:
        admin.exigir_ativa()
        admin.exigir(Permissao.VER_CONSUMO)
        nomes = {u.id: u.apelido for u in self._repos.usuarios.listar()}
        por_conta, por_caso, por_juiz, por_provedor = (defaultdict(int) for _ in range(4))
        total = simulado = 0
        for r in self._repos.consumos.listar():
            total += r.total
            if r.simulado:
                simulado += r.total
            por_conta[nomes.get(r.id_conta, f"(removida {r.id_conta})")] += r.total
            por_caso[r.id_caso] += r.total
            por_juiz[r.id_juiz] += r.total
            por_provedor[r.provedor] += r.total
        return {"total": total, "simulado": simulado, "real": total - simulado,
                "por_conta": dict(por_conta), "por_caso": dict(por_caso),
                "por_juiz": dict(por_juiz), "por_provedor": dict(por_provedor)}

    # --- cotas e tokens ---
    def _jogador(self, id_jogador) -> Jogador:
        alvo = self._repos.usuarios.buscar_por_id(id_jogador)
        if not isinstance(alvo, Jogador):
            raise DadosInvalidosException("A operação só se aplica a contas de jogador.")
        return alvo

    def _alterar_carteira(self, admin, id_jogador, permissao, mudanca):
        admin.exigir_ativa()
        admin.exigir(permissao)
        self._jogador(id_jogador)
        carteira = self._tokens.carteira_atual(id_jogador)
        mudanca(carteira)
        self._repos.carteiras.salvar(carteira)
        return carteira

    def definir_cota_diaria(self, admin, id_jogador, valor):
        return self._alterar_carteira(admin, id_jogador, Permissao.GERENCIAR_COTAS,
                                      lambda c: c.definir_cota_diaria(valor))

    def definir_cota_por_caso(self, admin, id_jogador, valor):
        return self._alterar_carteira(admin, id_jogador, Permissao.GERENCIAR_COTAS,
                                      lambda c: c.definir_cota_por_caso(valor))

    def conceder_tokens(self, admin, id_jogador, quantidade):
        return self._alterar_carteira(admin, id_jogador, Permissao.GERENCIAR_COTAS,
                                      lambda c: c.creditar(quantidade))

    def revogar_tokens(self, admin, id_jogador, quantidade):
        return self._alterar_carteira(admin, id_jogador, Permissao.GERENCIAR_COTAS,
                                      lambda c: c.revogar(quantidade))

    # --- contas ---
    def _alterar_conta(self, admin, id_jogador, acao):
        admin.exigir_ativa()
        admin.exigir(Permissao.GERENCIAR_CONTAS)
        jogador = self._jogador(id_jogador)  # admin só gerencia jogadores (nunca a si mesmo)
        acao(jogador)
        self._repos.usuarios.salvar(jogador)
        return jogador

    def suspender_conta(self, admin, id_jogador):
        return self._alterar_conta(admin, id_jogador, lambda j: j.suspender())

    def reativar_conta(self, admin, id_jogador):
        return self._alterar_conta(admin, id_jogador, lambda j: j.reativar())

    def remover_conta(self, admin, id_jogador):
        admin.exigir_ativa()
        admin.exigir(Permissao.GERENCIAR_CONTAS)
        jogador = self._jogador(id_jogador)
        jogador.marcar_excluida()
        self._repos.usuarios.remover(jogador.id)
        self._repos.carteiras.remover(jogador.id)

    # --- CRUD de pacotes ---
    def criar_pacote(self, admin, nome, tokens, **opcoes) -> PacoteTokens:
        admin.exigir_ativa()
        admin.exigir(Permissao.GERENCIAR_PACOTES)
        pacote = PacoteTokens(uuid.uuid4().hex[:8], nome, tokens, **opcoes)
        self._repos.pacotes.salvar(pacote)
        return pacote

    def listar_pacotes(self, admin) -> list:
        admin.exigir_ativa()
        admin.exigir(Permissao.GERENCIAR_PACOTES)
        return self._repos.pacotes.listar()

    def alterar_pacote(self, admin, id_pacote, **campos) -> PacoteTokens:
        admin.exigir_ativa()
        admin.exigir(Permissao.GERENCIAR_PACOTES)
        pacote = self._repos.pacotes.buscar_por_id(id_pacote)
        if pacote is None:
            raise DadosInvalidosException("Pacote inexistente.")
        pacote.alterar(**campos)
        self._repos.pacotes.salvar(pacote)
        return pacote

    def remover_pacote(self, admin, id_pacote) -> bool:
        admin.exigir_ativa()
        admin.exigir(Permissao.GERENCIAR_PACOTES)
        return self._repos.pacotes.remover(id_pacote)
