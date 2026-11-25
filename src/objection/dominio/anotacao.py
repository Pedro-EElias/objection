from datetime import datetime

from objection.dominio.validacao import exigir_texto
from objection.excecoes import DadosInvalidosException


class Anotacao:
    """Anotação do jogador no caderno de uma partida. Pode citar provas já descobertas (RN14)."""

    MAX_TITULO = 60
    MAX_TEXTO = 600

    def __init__(self, id_anotacao, id_partida, id_jogador, titulo, texto="", evidencias=(),
                 criada_em: datetime = None, atualizada_em: datetime = None):
        self._id = exigir_texto(id_anotacao, "id_anotacao")
        self._id_partida = exigir_texto(id_partida, "id_partida")
        self._id_jogador = exigir_texto(id_jogador, "id_jogador")
        self._titulo = self._validar_titulo(titulo)
        self._texto = self._validar_texto(texto)
        self._evidencias = tuple(evidencias)
        self._criada_em = criada_em or datetime.now()
        self._atualizada_em = atualizada_em or self._criada_em

    @classmethod
    def _validar_titulo(cls, titulo) -> str:
        titulo = exigir_texto(titulo, "título")
        if len(titulo) > cls.MAX_TITULO:
            raise DadosInvalidosException(f"O título deve ter no máximo {cls.MAX_TITULO} caracteres.")
        return titulo

    @classmethod
    def _validar_texto(cls, texto) -> str:
        if not isinstance(texto, str):
            raise DadosInvalidosException("O texto da anotação deve ser um texto.")
        texto = texto.strip()
        if len(texto) > cls.MAX_TEXTO:
            raise DadosInvalidosException(f"O texto deve ter no máximo {cls.MAX_TEXTO} caracteres.")
        return texto

    id = property(lambda s: s._id)
    id_partida = property(lambda s: s._id_partida)
    id_jogador = property(lambda s: s._id_jogador)
    titulo = property(lambda s: s._titulo)
    texto = property(lambda s: s._texto)
    evidencias = property(lambda s: s._evidencias)
    criada_em = property(lambda s: s._criada_em)
    atualizada_em = property(lambda s: s._atualizada_em)

    def editar(self, agora: datetime, titulo=None, texto=None, evidencias=None):
        novo_titulo = self._titulo if titulo is None else self._validar_titulo(titulo)
        novo_texto = self._texto if texto is None else self._validar_texto(texto)
        self._titulo, self._texto = novo_titulo, novo_texto
        if evidencias is not None:
            self._evidencias = tuple(evidencias)
        self._atualizada_em = agora
