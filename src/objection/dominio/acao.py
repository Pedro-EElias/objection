from abc import ABC, abstractmethod

from objection.config import CONFIG_PADRAO
from objection.excecoes import (
    AcaoJaExecutadaException,
    DadosInvalidosException,
    FaseInvalidaException,
    OrcamentoInsuficienteException,
    RequisitoNaoAtendidoException,
)
from objection.dominio.enums import Classificacao, FasePartida, TipoAlegacao
from objection.dominio.regras import calcular_probabilidade
from objection.dominio.resultado import AnaliseAlegacao, ResultadoAcao
from objection.dominio.validacao import exigir_intervalo, exigir_texto


class AcaoJogo(ABC):
    """Ação disponível ao jogador. Valida requisitos e CALCULA o resultado.

    A ação não altera a partida: devolve um ResultadoAcao e o MotorJogo o aplica.
    """

    def __init__(self, id_acao, texto, config=CONFIG_PADRAO):
        self._id = exigir_texto(id_acao, "id_acao")
        self._texto = exigir_texto(texto, "texto")
        self._config = config

    @property
    def id(self): return self._id

    @property
    def texto(self): return self._texto

    @property
    @abstractmethod
    def custo(self) -> int:
        """Créditos gastos (só na preparação)."""

    @property
    @abstractmethod
    def fase_permitida(self) -> FasePartida:
        """Fase em que a ação pode ser feita."""

    def validar(self, partida, caso):
        """Template method: regras comuns + gancho específico de cada ação."""
        partida.garantir_ativa()
        if partida.fase is not self.fase_permitida:
            raise FaseInvalidaException(
                f"A ação '{self._id}' só pode ser feita na fase "
                f"{self.fase_permitida.value}; a partida está em {partida.fase.value}."
            )
        if self._id in partida.acoes_executadas:
            raise AcaoJaExecutadaException(f"A ação '{self._id}' já foi executada nesta partida.")
        if self.custo > partida.orcamento:
            raise OrcamentoInsuficienteException(self.custo, partida.orcamento)
        self._validar_especifico(partida, caso)

    def _validar_especifico(self, partida, caso):
        """Gancho para requisitos próprios de cada subclasse."""

    @abstractmethod
    def executar(self, partida, caso, juiz, rng) -> ResultadoAcao:
        """Calcula o efeito sem alterar o estado."""


# ---------------------------------------------------------------- preparação
class Investigacao(AcaoJogo):
    def __init__(self, id_acao, texto, id_evidencia, config=CONFIG_PADRAO):
        super().__init__(id_acao, texto, config)
        self._id_evidencia = exigir_texto(id_evidencia, "id_evidencia")

    @property
    def custo(self): return self._config.custo_investigar

    @property
    def fase_permitida(self): return FasePartida.PREPARACAO

    @property
    def id_evidencia(self): return self._id_evidencia

    def _validar_especifico(self, partida, caso):
        caso.evidencia(self._id_evidencia)
        if self._id_evidencia in partida.evidencias_descobertas:
            raise AcaoJaExecutadaException(
                f"A evidência '{self._id_evidencia}' já foi descoberta."
            )

    def executar(self, partida, caso, juiz, rng):
        ev = caso.evidencia(self._id_evidencia)
        return ResultadoAcao(
            self._id, True,
            evidencias_reveladas=(ev.id,),
            motivos=(f"Evidência descoberta: {ev.descricao}",),
        )


class PrepararTestemunha(AcaoJogo):
    def __init__(self, id_acao, texto, id_testemunha, config=CONFIG_PADRAO):
        super().__init__(id_acao, texto, config)
        self._id_testemunha = exigir_texto(id_testemunha, "id_testemunha")

    @property
    def custo(self): return self._config.custo_testemunha

    @property
    def fase_permitida(self): return FasePartida.PREPARACAO

    @property
    def id_testemunha(self): return self._id_testemunha

    def _validar_especifico(self, partida, caso):
        if not caso.tem_testemunha(self._id_testemunha):
            raise DadosInvalidosException(f"A testemunha '{self._id_testemunha}' não existe no caso.")
        if self._id_testemunha in partida.testemunhas_preparadas:
            raise AcaoJaExecutadaException(f"A testemunha '{self._id_testemunha}' já foi preparada.")

    def executar(self, partida, caso, juiz, rng):
        return ResultadoAcao(
            self._id, True,
            marcadores=(f"testemunha:{self._id_testemunha}",),
            motivos=(f"Testemunha {self._id_testemunha} preparada.",),
        )


class PrepararAlibi(AcaoJogo):
    """Álibi ficcional: desbloqueia blefes de nível alto."""

    def __init__(self, id_acao, texto, afirmacao_alibi, config=CONFIG_PADRAO):
        super().__init__(id_acao, texto, config)
        self._afirmacao_alibi = exigir_texto(afirmacao_alibi, "afirmacao_alibi")

    @property
    def custo(self): return self._config.custo_alibi

    @property
    def fase_permitida(self): return FasePartida.PREPARACAO

    @property
    def afirmacao_alibi(self): return self._afirmacao_alibi

    def _validar_especifico(self, partida, caso):
        if partida.alibi_preparado:
            raise AcaoJaExecutadaException("O álibi já foi preparado nesta partida.")

    def executar(self, partida, caso, juiz, rng):
        return ResultadoAcao(
            self._id, True,
            marcadores=("alibi", f"afirmacao:{self._afirmacao_alibi}"),
            motivos=("Álibi preparado: blefes de nível alto liberados.",),
        )


class TentativaSuborno(AcaoJogo):
    """Ação abstrata e ficcional de alto risco."""

    def __init__(self, id_acao, texto, nivel_discricao=1, config=CONFIG_PADRAO):
        super().__init__(id_acao, texto, config)
        self._nivel_discricao = exigir_intervalo(nivel_discricao, "nivel_discricao", 1, 3)

    @property
    def custo(self): return self._config.custo_suborno

    @property
    def fase_permitida(self): return FasePartida.PREPARACAO

    @property
    def nivel_discricao(self): return self._nivel_discricao

    @property
    def risco(self): return 20 - 5 * self._nivel_discricao

    def _validar_especifico(self, partida, caso):
        if partida.suborno_tentado:
            raise AcaoJaExecutadaException("Só é possível tentar o suborno uma vez por partida.")

    def executar(self, partida, caso, juiz, rng):
        cfg = self._config
        analise = AnaliseAlegacao(
            tipo=TipoAlegacao.SUBORNO, classificacao=None, evidencias_sustentando=0,
            contradicoes=0, evidencias_ausentes=0,
            testemunhas_preparadas=len(partida.testemunhas_preparadas),
            alibi_preparado=partida.alibi_preparado, nivel_risco=0,
        )
        aval = juiz.avaliar(analise)
        prob = calcular_probabilidade(
            cfg.prob_base_suborno, aval.modificador, 0,
            partida.suspeita // cfg.divisor_penalidade_suspeita, self.risco, cfg)
        sucesso = rng.randint(1, 100) <= prob
        if sucesso:
            dc, ds = cfg.ganho_suborno, cfg.suspeita_suborno_sucesso
            texto = "Suborno aceito sem alarde."
        else:
            dc = -cfg.perda_suborno
            ds = round(cfg.suspeita_suborno_descoberto * aval.multiplicador_suspeita)
            texto = "Suborno descoberto: consequência grave."
        return ResultadoAcao(
            self._id, sucesso, delta_confianca=dc, delta_suspeita=ds,
            marcadores=("suborno",), probabilidade=prob,
            motivos=(f"Probabilidade de sucesso: {prob}%", *aval.motivos, texto),
        )


# ----------------------------------------------------------------- julgamento
class AcaoDeclaratoria(AcaoJogo, ABC):
    """Base de Argumento e Blefe: ambos fazem afirmações que o motor analisa."""

    def __init__(self, id_acao, texto, afirmacoes, evidencias_citadas=(), config=CONFIG_PADRAO):
        super().__init__(id_acao, texto, config)
        self._afirmacoes = tuple(exigir_texto(a, "afirmacao") for a in afirmacoes)
        if not self._afirmacoes:
            raise DadosInvalidosException("Uma alegação precisa de ao menos uma afirmação.")
        self._evidencias_citadas = tuple(evidencias_citadas)

    @property
    def custo(self): return 0  # no julgamento o que se gasta são rodadas, não créditos

    @property
    def fase_permitida(self): return FasePartida.JULGAMENTO

    @property
    def afirmacoes(self): return self._afirmacoes

    @property
    def evidencias_citadas(self): return self._evidencias_citadas

    def _validar_especifico(self, partida, caso):
        for id_ev in self._evidencias_citadas:
            caso.evidencia(id_ev)

    def _analisar(self, partida, caso, tipo, nivel_risco) -> AnaliseAlegacao:
        desc = partida.evidencias_descobertas
        ausentes = [e for e in self._evidencias_citadas if e not in desc]
        refutam = caso.evidencias_que_refutam(self._afirmacoes, desc)
        conflitos = caso.conflitos_com_declaracoes(self._afirmacoes, partida.afirmacoes)
        sustentam = caso.evidencias_que_sustentam(self._afirmacoes, desc)
        contradicoes = len(refutam) + conflitos
        if contradicoes:
            classe = Classificacao.CONTRADITORIO
        elif ausentes:
            classe = Classificacao.SEM_EVIDENCIA
        elif sustentam:
            classe = Classificacao.COERENTE
        else:
            classe = Classificacao.FRACO
        return AnaliseAlegacao(
            tipo=tipo, classificacao=classe, evidencias_sustentando=len(sustentam),
            contradicoes=contradicoes, evidencias_ausentes=len(ausentes),
            testemunhas_preparadas=len(partida.testemunhas_preparadas),
            alibi_preparado=partida.alibi_preparado, nivel_risco=nivel_risco,
        )

    def _resolver(self, partida, juiz, analise, risco, ganho, perda, susp_sucesso, susp_falha, rng):
        cfg = self._config
        aval = juiz.avaliar(analise)
        bonus = min(cfg.bonus_contexto_por_evidencia * analise.evidencias_sustentando,
                    cfg.bonus_contexto_maximo)
        prob = calcular_probabilidade(
            cfg.prob_base, aval.modificador, bonus,
            partida.suspeita // cfg.divisor_penalidade_suspeita, risco, cfg)
        sucesso = rng.randint(1, 100) <= prob
        susp = susp_sucesso if sucesso else susp_falha
        if analise.contradicoes:
            susp += cfg.suspeita_contradicao
        motivos = (
            f"Classificação: {analise.classificacao.value}",
            f"Probabilidade de sucesso: {prob}%",
            *aval.motivos,
            "Resultado: a alegação convenceu." if sucesso else "Resultado: a alegação não convenceu.",
        )
        return ResultadoAcao(
            self._id, sucesso,
            delta_confianca=ganho if sucesso else -perda,
            delta_suspeita=round(susp * aval.multiplicador_suspeita),
            marcadores=tuple(f"afirmacao:{a}" for a in self._afirmacoes),
            motivos=motivos, probabilidade=prob, classificacao=analise.classificacao,
        )


class Argumento(AcaoDeclaratoria):
    """Interpretação dos fatos. Rende mais quanto mais provas descobertas o sustentam."""

    def executar(self, partida, caso, juiz, rng):
        cfg = self._config
        analise = self._analisar(partida, caso, TipoAlegacao.ARGUMENTO, 0)
        ganho = cfg.ganho_argumento + cfg.ganho_por_evidencia * analise.evidencias_sustentando
        return self._resolver(partida, juiz, analise, 0, ganho, cfg.perda_argumento,
                              0, cfg.suspeita_falha_argumento, rng)


class Blefe(AcaoDeclaratoria):
    """Afirmação arriscada. Quanto maior o nível, maior o ganho, o risco e a suspeita."""

    def __init__(self, id_acao, texto, afirmacoes, nivel=1, evidencias_citadas=(), config=CONFIG_PADRAO):
        super().__init__(id_acao, texto, afirmacoes, evidencias_citadas, config)
        self._nivel = exigir_intervalo(nivel, "nivel", 1, 3)

    @property
    def nivel(self): return self._nivel

    def _validar_especifico(self, partida, caso):
        super()._validar_especifico(partida, caso)
        if self._nivel >= 3 and not partida.alibi_preparado:
            raise RequisitoNaoAtendidoException("Blefe de nível 3 exige um álibi preparado.")

    def executar(self, partida, caso, juiz, rng):
        cfg = self._config
        analise = self._analisar(partida, caso, TipoAlegacao.BLEFE, self._nivel)
        return self._resolver(
            partida, juiz, analise,
            risco=cfg.risco_blefe_por_nivel * self._nivel,
            ganho=cfg.ganho_blefe_base + cfg.ganho_blefe_por_nivel * self._nivel,
            perda=cfg.perda_blefe,
            susp_sucesso=3 * self._nivel,
            susp_falha=10 + 5 * self._nivel,
            rng=rng,
        )
