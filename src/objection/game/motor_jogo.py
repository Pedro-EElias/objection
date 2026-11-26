import random

from objection.config import CONFIG_PADRAO
from objection.dominio.enums import FasePartida, Permissao, ResultadoVeredito
from objection.dominio.partida import Partida
from objection.dominio.regras import faixa_confianca
from objection.dominio.resultado import HistoricoEvento, Veredito
from objection.excecoes import FaseInvalidaException


class MotorJogo:
    """Única parte autorizada a alterar o estado da partida e a decidir o veredito."""

    def __init__(self, config=CONFIG_PADRAO, semente=None):
        self._config = config
        self._rng = random.Random(semente)

    def iniciar_partida(self, caso, id_partida, usuario=None, id_juiz=None, nome=None) -> Partida:
        id_jogador = None
        if usuario is not None:
            usuario.exigir_ativa()  # RN20: conta suspensa não inicia partida
            usuario.exigir(Permissao.JOGAR)
            id_jogador = usuario.id
        c = self._config
        return Partida(id_partida, caso.id, c.orcamento_inicial,
                       c.confianca_inicial, c.suspeita_inicial, id_jogador, id_juiz, nome)

    def iniciar_julgamento(self, partida):
        partida.garantir_ativa()
        partida.mudar_fase(FasePartida.JULGAMENTO)

    def abandonar(self, partida):
        partida.garantir_ativa()
        partida.mudar_fase(FasePartida.ABANDONADA)

    def executar_acao(self, partida, caso, juiz, acao, usuario=None):
        # 0) autorização do perfil (RN11)
        if usuario is not None:
            usuario.exigir_ativa()
            usuario.exigir(acao.permissao_exigida)
        # 1) valida sem alterar nada; se falhar, o estado continua intacto
        acao.validar(partida, caso)
        # 2) calcula o resultado (função sem efeito colateral na partida)
        r = acao.executar(partida, caso, juiz, self._rng)
        # 3) aplica
        partida.debitar(acao.custo)
        partida.ajustar_confianca(r.delta_confianca)
        partida.ajustar_suspeita(r.delta_suspeita)
        for id_ev in r.evidencias_reveladas:
            partida.registrar_evidencia(id_ev)
        for marcador in r.marcadores:
            self._aplicar_marcador(partida, marcador)
        partida.marcar_acao_executada(acao.id)
        if acao.fase_permitida is FasePartida.JULGAMENTO:
            partida.avancar_rodada()
        partida.registrar_evento(HistoricoEvento(
            rodada=partida.rodada, id_acao=acao.id, descricao=acao.texto,
            sucesso=r.sucesso, delta_confianca=r.delta_confianca,
            delta_suspeita=r.delta_suspeita, motivos=r.motivos))
        self._verificar_fim_do_julgamento(partida)
        return r

    def registrar_conduta_inadequada(self, partida):
        """RN24: texto que tenta manipular o juiz aumenta a suspeita. Só o motor altera o estado."""
        partida.garantir_ativa()
        if partida.fase is not FasePartida.JULGAMENTO:
            raise FaseInvalidaException("A fala livre só é possível durante o julgamento.")
        delta = self._config.suspeita_conduta_inadequada
        partida.ajustar_suspeita(delta)
        partida.registrar_evento(HistoricoEvento(
            rodada=partida.rodada, id_acao="conduta-inadequada",
            descricao="Fala fora das regras do tribunal", sucesso=False,
            delta_confianca=0, delta_suspeita=delta,
            motivos=("Conduta inadequada: o juiz desconfia de quem tenta manipular a sessão.",)))
        self._verificar_fim_do_julgamento(partida)

    def emitir_veredito(self, partida, caso) -> Veredito:
        partida.garantir_ativa()
        if partida.fase is FasePartida.JULGAMENTO:
            partida.mudar_fase(FasePartida.DELIBERACAO)
        partida.mudar_fase(FasePartida.ENCERRADA)  # falha se vier da preparação
        favoravel = (partida.confianca >= caso.confianca_minima_vitoria
                     and partida.suspeita < caso.suspeita_maxima_vitoria)
        motivos = (
            f"Confiança final {partida.confianca} (mínimo {caso.confianca_minima_vitoria}).",
            f"Suspeita final {partida.suspeita} (limite {caso.suspeita_maxima_vitoria}).",
        )
        veredito = Veredito(
            ResultadoVeredito.FAVORAVEL if favoravel else ResultadoVeredito.DESFAVORAVEL,
            partida.confianca, partida.suspeita, faixa_confianca(partida.confianca), motivos)
        partida.definir_veredito(veredito)
        return veredito

    # --- internos ---
    @staticmethod
    def _aplicar_marcador(partida, marcador: str):
        tipo, _, valor = marcador.partition(":")
        if tipo == "testemunha":
            partida.marcar_testemunha_preparada(valor)
        elif tipo == "alibi":
            partida.marcar_alibi_preparado()
        elif tipo == "suborno":
            partida.marcar_suborno_tentado()
        elif tipo == "afirmacao":
            partida.registrar_afirmacao(valor)

    def _verificar_fim_do_julgamento(self, partida):
        if partida.fase is not FasePartida.JULGAMENTO:
            return
        if partida.suspeita >= self._config.suspeita_maxima or partida.rodada >= self._config.max_rodadas:
            partida.mudar_fase(FasePartida.DELIBERACAO)
