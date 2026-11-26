import logging
from dataclasses import dataclass, replace
from typing import Optional

from objection.excecoes import (
    CotaDoCasoExcedidaException,
    InterpretacaoIndisponivelException,
    ProvedorIAIndisponivelException,
    RespostaIAInvalidaException,
    TokensInsuficientesException,
)
from objection.ia.configuracao import ConfiguracaoIA
from objection.ia.contexto import EVENTOS_OBJECAO
from objection.ia.gemini import ProvedorGemini
from objection.ia.local import ProvedorLocal
from objection.ia.seguranca import detectar_injecao

log = logging.getLogger("objection.ia")


@dataclass(frozen=True)
class ResultadoDialogo:
    reacao: object
    provedor: str
    fallback_motivo: Optional[str]   # por que não usou IA (None se usou, ou se não foi pedida)


@dataclass(frozen=True)
class ResultadoInterpretacao:
    interpretacao: Optional[object]
    provedor: str
    conduta_inadequada: bool


def criar_provedores(config: ConfiguracaoIA) -> dict:
    """Monta os provedores disponíveis. O local sempre existe."""
    provedores = {"local": ProvedorLocal()}
    if config.gemini_configurado:
        provedores["gemini"] = ProvedorGemini(config)
    return provedores


class ServicoDialogo:
    """Coordena juiz, provedores e energia. Se algo falhar, o jogador continua com falas locais."""

    def __init__(self, provedores: dict, cadeias: dict, servico_tokens):
        self._provedores = provedores
        self._cadeias = cadeias
        self._tokens = servico_tokens

    def interpretar(self, usuario, id_caso, juiz, contexto) -> ResultadoInterpretacao:
        """Interpreta um argumento livre. Sem IA utilizável, levanta InterpretacaoIndisponivelException."""
        # Texto que tenta dar ordens ao modelo nem chega a ele (RN24: conduta inadequada).
        if detectar_injecao(contexto.texto):
            log.warning("Tentativa de manipulação detectada; a IA não foi chamada.")
            return ResultadoInterpretacao(None, "local", True)
        nomes = [n for n in self._cadeias.get(juiz.id, ()) if n != "local" and n in self._provedores]
        if not nomes:
            raise InterpretacaoIndisponivelException(
                "Este juiz não usa IA, então só aceita as opções prontas.")
        usuario.exigir_ativa()
        for nome in nomes:
            provedor = self._provedores[nome]
            try:
                self._tokens.autorizar_chamada(usuario, id_caso, provedor.estimar_tokens_interpretacao(contexto))
            except TokensInsuficientesException as erro:
                raise InterpretacaoIndisponivelException(
                    f"{erro} Use as opções prontas.") from None
            except CotaDoCasoExcedidaException:
                raise InterpretacaoIndisponivelException(
                    "A cota de IA restante para este caso não cobre esta chamada. "
                    "Use as opções prontas; a cota recarrega amanhã."
                ) from None
            try:
                interpretacao = provedor.interpretar(contexto)
            except (ProvedorIAIndisponivelException, RespostaIAInvalidaException) as erro:
                log.warning("Provedor %s falhou ao interpretar (%s).", nome, type(erro).__name__)
                continue
            self._tokens.registrar_consumo(usuario, id_caso, juiz.id, nome, interpretacao.tokens_entrada,
                                           interpretacao.tokens_saida, simulado=False)
            return ResultadoInterpretacao(interpretacao, nome, False)
        raise InterpretacaoIndisponivelException(
            "A IA não conseguiu interpretar o argumento agora. Use as opções prontas.")

    def tem_ia(self, id_juiz: str) -> bool:
        return any(n != "local" and n in self._provedores for n in self._cadeias.get(id_juiz, ()))

    def gerar(self, usuario, id_caso, juiz, contexto, usar_ia: bool) -> ResultadoDialogo:
        # 1) Cadeia de provedores online, com energia conferida antes de cada chamada.
        motivo = None
        if usar_ia:
            for nome in self._cadeias.get(juiz.id, ()):
                provedor = self._provedores.get(nome)
                if provedor is None or nome == "local":
                    continue
                try:
                    self._tokens.autorizar_chamada(usuario, id_caso, provedor.estimar_tokens(juiz, contexto))
                except TokensInsuficientesException:
                    motivo = "sem_energia"
                    break
                except CotaDoCasoExcedidaException:
                    motivo = "cota_caso"
                    break
                try:
                    reacao = provedor.gerar_reacao(juiz, contexto)
                except (ProvedorIAIndisponivelException, RespostaIAInvalidaException) as erro:
                    log.warning("Provedor %s falhou (%s).", nome, type(erro).__name__)
                    motivo = "indisponivel" if isinstance(erro, ProvedorIAIndisponivelException) else "resposta_invalida"
                    continue
                reacao = replace(reacao, objecao=contexto.evento in EVENTOS_OBJECAO)  # a objeção é do motor
                self._tokens.registrar_consumo(usuario, id_caso, juiz.id, nome, reacao.tokens_entrada,
                                               reacao.tokens_saida, simulado=False)
                return ResultadoDialogo(reacao, nome, None)
        # 2) Fallback local (também é o modo offline).
        return ResultadoDialogo(self._local(usuario, id_caso, juiz, contexto), "local", motivo)

    def _local(self, usuario, id_caso, juiz, contexto):
        reacao = self._provedores["local"].gerar_reacao(juiz, contexto)
        # O consumo local entra no livro como simulado e NÃO desconta energia.
        self._tokens.registrar_consumo(usuario, id_caso, juiz.id, "local", reacao.tokens_entrada,
                                       reacao.tokens_saida, simulado=True)
        return reacao
