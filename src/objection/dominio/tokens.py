from datetime import date, datetime

from objection.excecoes import (
    CotaDoCasoExcedidaException,
    DadosInvalidosException,
    TokensInsuficientesException,
)
from objection.dominio.validacao import exigir_intervalo, exigir_texto

_MAX = 10_000_000


class CarteiraTokens:
    """Energia de IA da conta. O jogador vê só um percentual; o admin vê os tokens reais."""

    def __init__(self, id_conta, cota_diaria, cota_por_caso, saldo=None,
                 data_recarga=None, consumo_por_caso=None):
        self._id_conta = exigir_texto(id_conta, "id_conta")
        self._cota_diaria = exigir_intervalo(cota_diaria, "cota_diaria", 0, _MAX)
        self._cota_por_caso = exigir_intervalo(cota_por_caso, "cota_por_caso", 0, _MAX)
        self._saldo = exigir_intervalo(self._cota_diaria if saldo is None else saldo, "saldo", 0, _MAX)
        self._data_recarga = data_recarga
        self._consumo_por_caso = dict(consumo_por_caso or {})

    @property
    def id_conta(self): return self._id_conta

    @property
    def id(self): return self._id_conta

    @property
    def cota_diaria(self): return self._cota_diaria

    @property
    def cota_por_caso(self): return self._cota_por_caso

    @property
    def saldo(self): return self._saldo

    @property
    def data_recarga(self): return self._data_recarga

    @property
    def consumo_por_caso(self): return dict(self._consumo_por_caso)

    @property
    def energia_percentual(self) -> int:
        """O que o jogador enxerga (ex.: 90 de 100). Nunca passa de 100."""
        if self._cota_diaria == 0:
            return 0
        return min(100, round(100 * self._saldo / self._cota_diaria))

    def recarregar_se_novo_dia(self, hoje: date) -> bool:
        """Recarga diária: completa até a cota, sem acumular a sobra do dia anterior.

        Tokens extras (ofertas, concessão do admin) acima da cota são preservados.
        Devolve True se recarregou.
        """
        if self._data_recarga == hoje:
            return False
        self._saldo = max(self._saldo, self._cota_diaria)
        self._consumo_por_caso = {}
        self._data_recarga = hoje
        return True

    def autorizar(self, estimativa: int, id_caso: str):
        """Confere saldo e cota do caso ANTES de uma chamada online (RN16)."""
        if estimativa > self._saldo:
            raise TokensInsuficientesException(estimativa, self._saldo)
        usado = self._consumo_por_caso.get(id_caso, 0)
        if usado + estimativa > self._cota_por_caso:
            raise CotaDoCasoExcedidaException(
                f"O limite do caso '{id_caso}' no dia foi atingido ({usado}/{self._cota_por_caso})."
            )

    def consumir(self, tokens: int, id_caso: str):
        """Desconta o consumo real. O saldo nunca fica negativo (RN23)."""
        exigir_intervalo(tokens, "tokens", 0, _MAX)
        self._saldo = max(0, self._saldo - tokens)
        self._consumo_por_caso[id_caso] = self._consumo_por_caso.get(id_caso, 0) + tokens

    def creditar(self, tokens: int):
        self._saldo += exigir_intervalo(tokens, "tokens", 0, _MAX)

    def revogar(self, tokens: int):
        self._saldo = max(0, self._saldo - exigir_intervalo(tokens, "tokens", 0, _MAX))

    def definir_cota_diaria(self, valor: int):
        self._cota_diaria = exigir_intervalo(valor, "cota_diaria", 0, _MAX)

    def definir_cota_por_caso(self, valor: int):
        self._cota_por_caso = exigir_intervalo(valor, "cota_por_caso", 0, _MAX)


class RegistroConsumo:
    """Uma linha do livro de consumo: quanto cada chamada gastou."""

    def __init__(self, id_registro, id_conta, id_caso, id_juiz, provedor,
                 tokens_entrada, tokens_saida, simulado, momento: datetime):
        self._id = exigir_texto(id_registro, "id_registro")
        self._id_conta = exigir_texto(id_conta, "id_conta")
        self._id_caso = exigir_texto(id_caso, "id_caso")
        self._id_juiz = exigir_texto(id_juiz, "id_juiz")
        self._provedor = exigir_texto(provedor, "provedor")
        self._tokens_entrada = exigir_intervalo(tokens_entrada, "tokens_entrada", 0, _MAX)
        self._tokens_saida = exigir_intervalo(tokens_saida, "tokens_saida", 0, _MAX)
        self._simulado = bool(simulado)
        self._momento = momento

    id = property(lambda s: s._id)
    id_conta = property(lambda s: s._id_conta)
    id_caso = property(lambda s: s._id_caso)
    id_juiz = property(lambda s: s._id_juiz)
    provedor = property(lambda s: s._provedor)
    tokens_entrada = property(lambda s: s._tokens_entrada)
    tokens_saida = property(lambda s: s._tokens_saida)
    simulado = property(lambda s: s._simulado)
    momento = property(lambda s: s._momento)

    @property
    def total(self) -> int:
        return self._tokens_entrada + self._tokens_saida


class PacoteTokens:
    """Oferta simulada (sem dinheiro real) que concede tokens extras."""

    def __init__(self, id_pacote, nome, tokens, limite_por_conta=None,
                 uma_por_dia=False, validade_ate=None, ativo=True):
        self._id = exigir_texto(id_pacote, "id_pacote")
        self._nome = exigir_texto(nome, "nome")
        self._tokens = exigir_intervalo(tokens, "tokens", 1, _MAX)
        if limite_por_conta is not None:
            exigir_intervalo(limite_por_conta, "limite_por_conta", 1, 100_000)
        self._limite_por_conta = limite_por_conta
        self._uma_por_dia = bool(uma_por_dia)
        self._validade_ate = validade_ate
        self._ativo = bool(ativo)

    id = property(lambda s: s._id)
    nome = property(lambda s: s._nome)
    tokens = property(lambda s: s._tokens)
    limite_por_conta = property(lambda s: s._limite_por_conta)
    uma_por_dia = property(lambda s: s._uma_por_dia)
    validade_ate = property(lambda s: s._validade_ate)
    ativo = property(lambda s: s._ativo)

    def esta_disponivel(self, hoje: date) -> bool:
        return self._ativo and (self._validade_ate is None or hoje <= self._validade_ate)

    def alterar(self, nome=None, tokens=None, limite_por_conta=..., uma_por_dia=None,
                validade_ate=..., ativo=None):
        """Alteração parcial (CRUD). Usa ... para distinguir 'não mexer' de 'limpar'."""
        novo = PacoteTokens(
            self._id,
            self._nome if nome is None else nome,
            self._tokens if tokens is None else tokens,
            self._limite_por_conta if limite_por_conta is ... else limite_por_conta,
            self._uma_por_dia if uma_por_dia is None else uma_por_dia,
            self._validade_ate if validade_ate is ... else validade_ate,
            self._ativo if ativo is None else ativo,
        )
        self.__dict__.update(novo.__dict__)


class ResgateOferta:
    def __init__(self, id_resgate, id_conta, id_pacote, data: date, tokens: int):
        self._id = exigir_texto(id_resgate, "id_resgate")
        self._id_conta = exigir_texto(id_conta, "id_conta")
        self._id_pacote = exigir_texto(id_pacote, "id_pacote")
        self._data = data
        self._tokens = tokens

    id = property(lambda s: s._id)
    id_conta = property(lambda s: s._id_conta)
    id_pacote = property(lambda s: s._id_pacote)
    data = property(lambda s: s._data)
    tokens = property(lambda s: s._tokens)
