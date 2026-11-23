import hashlib
import hmac
import re
import secrets
from abc import ABC, abstractmethod

from objection.config import CONFIG_PADRAO
from objection.dominio.enums import NivelJogador, Permissao, StatusConta
from objection.dominio.validacao import exigir_texto
from objection.excecoes import (
    AcessoNegadoException,
    ContaSuspensaException,
    DadosInvalidosException,
    TransicaoInvalidaException,
)

_PADRAO_APELIDO = re.compile(r"[A-Za-z0-9_.-]{3,20}")


def _validar_apelido(apelido) -> str:
    apelido = exigir_texto(apelido, "apelido")
    if not _PADRAO_APELIDO.fullmatch(apelido):
        raise DadosInvalidosException("O apelido deve ter de 3 a 20 caracteres (letras, números, _ . -).")
    return apelido


def _validar_senha(senha) -> str:
    if not isinstance(senha, str) or len(senha) < 6:
        raise DadosInvalidosException("A senha deve ter ao menos 6 caracteres.")
    return senha


def _calcular_hash(senha: str, salt_hex: str, iteracoes: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), iteracoes).hex()


class Usuario(ABC):
    """Conta do sistema. Os perfis (Administrador, Jogador) definem as permissões."""

    ITERACOES_HASH = 100_000

    def __init__(self, id_usuario, apelido, senha_hash, salt, iteracoes, status=StatusConta.ATIVA):
        self._id = exigir_texto(id_usuario, "id_usuario")
        self._apelido = _validar_apelido(apelido)
        self._senha_hash = exigir_texto(senha_hash, "senha_hash")
        self._salt = exigir_texto(salt, "salt")
        self._iteracoes = iteracoes
        self._status = status

    @staticmethod
    def _dados_de_senha(senha):
        _validar_senha(senha)
        salt = secrets.token_bytes(16).hex()
        iteracoes = Usuario.ITERACOES_HASH
        return _calcular_hash(senha, salt, iteracoes), salt, iteracoes

    # --- leitura ---
    @property
    def id(self): return self._id

    @property
    def apelido(self): return self._apelido

    @property
    def status(self): return self._status

    @property
    def senha_hash(self): return self._senha_hash

    @property
    def salt(self): return self._salt

    @property
    def iteracoes(self): return self._iteracoes

    @property
    @abstractmethod
    def perfil(self) -> str:
        """Nome do perfil."""

    @abstractmethod
    def pode(self, permissao: Permissao) -> bool:
        """Cada perfil responde de forma diferente (polimorfismo)."""

    # --- autorização ---
    def exigir(self, permissao: Permissao):
        if not self.pode(permissao):
            raise AcessoNegadoException(
                f"O perfil {self.perfil} não tem a permissão '{permissao.value}'."
            )

    def exigir_ativa(self):
        if self._status is not StatusConta.ATIVA:
            raise ContaSuspensaException(f"A conta '{self._apelido}' está {self._status.value}.")

    # --- senha e dados ---
    def verificar_senha(self, senha) -> bool:
        if not isinstance(senha, str):
            return False
        tentativa = _calcular_hash(senha, self._salt, self._iteracoes)
        return hmac.compare_digest(tentativa, self._senha_hash)

    def definir_senha(self, nova_senha):
        self._senha_hash, self._salt, self._iteracoes = self._dados_de_senha(nova_senha)

    def definir_apelido(self, novo_apelido):
        self._apelido = _validar_apelido(novo_apelido)

    # --- estado da conta ---
    def suspender(self):
        self._mudar_status(StatusConta.SUSPENSA, {StatusConta.ATIVA})

    def reativar(self):
        self._mudar_status(StatusConta.ATIVA, {StatusConta.SUSPENSA})

    def marcar_excluida(self):
        self._mudar_status(StatusConta.EXCLUIDA, {StatusConta.ATIVA, StatusConta.SUSPENSA})

    def _mudar_status(self, novo, origens_validas):
        if self._status not in origens_validas:
            raise TransicaoInvalidaException(self._status, novo)
        self._status = novo


class Administrador(Usuario):
    """Gerencia contas, cotas, consumo de tokens e pacotes. Não joga."""

    PERMISSOES_PADRAO = frozenset({
        Permissao.VER_CONSUMO, Permissao.GERENCIAR_COTAS,
        Permissao.GERENCIAR_CONTAS, Permissao.GERENCIAR_PACOTES,
    })

    def __init__(self, id_usuario, apelido, senha_hash, salt, iteracoes,
                 status=StatusConta.ATIVA, permissoes=None):
        super().__init__(id_usuario, apelido, senha_hash, salt, iteracoes, status)
        self._permissoes = frozenset(permissoes) if permissoes is not None else self.PERMISSOES_PADRAO

    @classmethod
    def novo(cls, id_usuario, apelido, senha):
        h, salt, it = Usuario._dados_de_senha(senha)
        return cls(id_usuario, apelido, h, salt, it)

    @property
    def perfil(self): return "administrador"

    @property
    def permissoes(self): return self._permissoes

    def pode(self, permissao):
        return permissao in self._permissoes


class Jogador(Usuario):
    """Joga os casos. Começa Novato e vira Veterano com a experiência (RN12)."""

    _PERMISSOES_NOVATO = frozenset({Permissao.JOGAR, Permissao.RESGATAR_OFERTAS})
    _PERMISSOES_VETERANO = _PERMISSOES_NOVATO | {
        Permissao.USAR_BLEFE, Permissao.USAR_SUBORNO, Permissao.ARGUMENTO_LIVRE,
    }

    def __init__(self, id_usuario, apelido, senha_hash, salt, iteracoes,
                 status=StatusConta.ATIVA, nivel=NivelJogador.NOVATO,
                 partidas_concluidas=(), vitorias=0, config=CONFIG_PADRAO):
        super().__init__(id_usuario, apelido, senha_hash, salt, iteracoes, status)
        self._nivel = nivel
        self._partidas_concluidas = set(partidas_concluidas)
        self._vitorias = vitorias
        self._config = config

    @classmethod
    def novo(cls, id_usuario, apelido, senha):
        h, salt, it = Usuario._dados_de_senha(senha)
        return cls(id_usuario, apelido, h, salt, it)

    @property
    def perfil(self): return "jogador"

    @property
    def nivel(self): return self._nivel

    @property
    def partidas_concluidas(self): return frozenset(self._partidas_concluidas)

    @property
    def vitorias(self): return self._vitorias

    def pode(self, permissao):
        permitidas = (self._PERMISSOES_VETERANO if self._nivel is NivelJogador.VETERANO
                      else self._PERMISSOES_NOVATO)
        return permissao in permitidas

    def registrar_partida_concluida(self, id_partida: str, venceu: bool) -> bool:
        """Conta cada partida uma única vez. Devolve True se esta chamada promoveu o jogador."""
        if id_partida in self._partidas_concluidas:
            return False
        self._partidas_concluidas.add(id_partida)
        if venceu:
            self._vitorias += 1
        if (self._nivel is NivelJogador.NOVATO
                and len(self._partidas_concluidas) >= self._config.partidas_para_promocao
                and self._vitorias >= self._config.vitorias_para_promocao):
            self._nivel = NivelJogador.VETERANO
            return True
        return False
