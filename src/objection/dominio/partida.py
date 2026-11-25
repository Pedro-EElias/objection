from objection.excecoes import (
    DadosInvalidosException,
    OrcamentoInsuficienteException,
    PartidaEncerradaException,
    TransicaoInvalidaException,
)
from objection.dominio.enums import FasePartida
from objection.dominio.regras import limitar
from objection.dominio.validacao import exigir_intervalo, exigir_texto


class Partida:
    """Estado de um julgamento. Máquina de estados com transições validadas.

    Quem altera os números do jogo é o MotorJogo; a IA nunca toca nesta classe.
    """

    _TRANSICOES = {
        FasePartida.PREPARACAO: {FasePartida.JULGAMENTO, FasePartida.ABANDONADA},
        FasePartida.JULGAMENTO: {FasePartida.DELIBERACAO, FasePartida.ABANDONADA},
        FasePartida.DELIBERACAO: {FasePartida.ENCERRADA},
        FasePartida.ENCERRADA: set(),
        FasePartida.ABANDONADA: set(),
    }

    def __init__(self, id_partida, id_caso, orcamento, confianca, suspeita,
                 id_jogador=None, id_juiz=None, nome=None):
        self._id = exigir_texto(id_partida, "id_partida")
        self._id_caso = exigir_texto(id_caso, "id_caso")
        self._id_jogador = id_jogador
        self._id_juiz = id_juiz
        self._nome = exigir_texto(nome, "nome") if nome is not None else f"Partida {self._id}"
        self._orcamento = exigir_intervalo(orcamento, "orcamento", 0, 1_000_000)
        self._confianca = exigir_intervalo(confianca, "confianca", 0, 100)
        self._suspeita = exigir_intervalo(suspeita, "suspeita", 0, 100)
        self._fase = FasePartida.PREPARACAO
        self._evidencias = set()
        self._testemunhas = set()
        self._alibi = False
        self._suborno = False
        self._acoes = set()
        self._afirmacoes = []
        self._rodada = 0
        self._historico = []
        self._veredito = None
        self._versao = 1  # base do lock otimista (etapa de persistência)

    # --- leitura ---
    @property
    def id(self): return self._id

    @property
    def id_caso(self): return self._id_caso

    @property
    def id_jogador(self): return self._id_jogador

    @property
    def id_juiz(self): return self._id_juiz

    @property
    def nome(self): return self._nome

    @property
    def fase(self): return self._fase

    @property
    def orcamento(self): return self._orcamento

    @property
    def confianca(self): return self._confianca

    @property
    def suspeita(self): return self._suspeita

    @property
    def rodada(self): return self._rodada

    @property
    def versao(self): return self._versao

    @property
    def evidencias_descobertas(self): return frozenset(self._evidencias)

    @property
    def testemunhas_preparadas(self): return frozenset(self._testemunhas)

    @property
    def alibi_preparado(self): return self._alibi

    @property
    def suborno_tentado(self): return self._suborno

    @property
    def acoes_executadas(self): return frozenset(self._acoes)

    @property
    def afirmacoes(self): return tuple(self._afirmacoes)

    @property
    def historico(self): return tuple(self._historico)

    @property
    def veredito(self): return self._veredito

    @property
    def encerrada(self):
        return self._fase in (FasePartida.ENCERRADA, FasePartida.ABANDONADA)

    # --- escrita (usada pelo MotorJogo) ---
    def _tocar(self):
        self._versao += 1

    def garantir_ativa(self):
        if self.encerrada:
            raise PartidaEncerradaException(
                f"A partida '{self._id}' está {self._fase.value} e não aceita novas ações."
            )

    def debitar(self, valor: int):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O valor a debitar deve ser um inteiro não negativo.")
        if valor > self._orcamento:
            raise OrcamentoInsuficienteException(valor, self._orcamento)
        self._orcamento -= valor
        self._tocar()

    def ajustar_confianca(self, delta: int):
        self._confianca = limitar(self._confianca + delta, 0, 100)
        self._tocar()

    def ajustar_suspeita(self, delta: int):
        self._suspeita = limitar(self._suspeita + delta, 0, 100)
        self._tocar()

    def registrar_evidencia(self, id_evidencia: str):
        self._evidencias.add(id_evidencia)
        self._tocar()

    def marcar_testemunha_preparada(self, id_testemunha: str):
        self._testemunhas.add(id_testemunha)
        self._tocar()

    def marcar_alibi_preparado(self):
        self._alibi = True
        self._tocar()

    def marcar_suborno_tentado(self):
        self._suborno = True
        self._tocar()

    def registrar_afirmacao(self, afirmacao: str):
        if afirmacao not in self._afirmacoes:
            self._afirmacoes.append(afirmacao)
        self._tocar()

    def marcar_acao_executada(self, id_acao: str):
        self._acoes.add(id_acao)
        self._tocar()

    def avancar_rodada(self):
        self._rodada += 1
        self._tocar()

    def registrar_evento(self, evento):
        self._historico.append(evento)
        self._tocar()

    def definir_veredito(self, veredito):
        self._veredito = veredito
        self._tocar()

    def renomear(self, novo_nome: str):
        novo_nome = exigir_texto(novo_nome, "nome")
        if not 3 <= len(novo_nome) <= 60:
            raise DadosInvalidosException("O nome da partida deve ter de 3 a 60 caracteres.")
        self._nome = novo_nome
        self._tocar()

    @classmethod
    def restaurar(cls, id_partida, id_caso, id_jogador, id_juiz, nome, fase, orcamento, confianca,
                  suspeita, evidencias, testemunhas, alibi, suborno, acoes, afirmacoes, rodada,
                  historico, veredito, versao):
        """Reconstrói uma partida salva (usado só pela persistência)."""
        p = cls(id_partida, id_caso, orcamento, confianca, suspeita, id_jogador, id_juiz, nome)
        p._fase = fase
        p._evidencias = set(evidencias)
        p._testemunhas = set(testemunhas)
        p._alibi = bool(alibi)
        p._suborno = bool(suborno)
        p._acoes = set(acoes)
        p._afirmacoes = list(afirmacoes)
        p._rodada = rodada
        p._historico = list(historico)
        p._veredito = veredito
        p._versao = versao
        return p

    def mudar_fase(self, nova: FasePartida):
        if nova not in self._TRANSICOES[self._fase]:
            raise TransicaoInvalidaException(self._fase, nova)
        self._fase = nova
        self._tocar()
