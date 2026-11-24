from abc import ABC, abstractmethod

from objection.dominio.enums import Classificacao, TipoAlegacao
from objection.dominio.resultado import AnaliseAlegacao, AvaliacaoJuiz
from objection.dominio.validacao import exigir_texto
from objection.excecoes import DadosInvalidosException


class Juiz(ABC):
    """Juiz abstrato. Avalia uma análise e devolve um parecer; nunca altera o estado."""

    ID = "juiz"

    def __init__(self, nome, titulo, perfil, estilo_fala):
        self._nome = exigir_texto(nome, "nome")
        self._titulo = exigir_texto(titulo, "titulo")
        self._perfil = exigir_texto(perfil, "perfil")
        self._estilo_fala = exigir_texto(estilo_fala, "estilo_fala")

    @property
    def id(self): return type(self).ID

    @property
    def nome(self): return self._nome

    @property
    def titulo(self): return self._titulo

    @property
    def perfil(self): return self._perfil

    @property
    def estilo_fala(self): return self._estilo_fala

    @abstractmethod
    def avaliar(self, analise: AnaliseAlegacao) -> AvaliacaoJuiz:
        """Cada juiz aplica regras próprias (polimorfismo)."""


class JuizFormalista(Juiz):
    """Augusto Valença: valoriza provas e pune contradições com mais suspeita."""

    ID = "formalista"

    def __init__(self, nome="Augusto Valença", titulo="Juiz Titular",
                 peso_evidencia=8, penalidade_sem_prova=15, multiplicador_contradicao=1.5):
        super().__init__(nome, titulo,
                         "Rigoroso, metódico e atento a provas e contradições.",
                         "Formal, preciso e contido.")
        self._peso_evidencia = peso_evidencia
        self._penalidade_sem_prova = penalidade_sem_prova
        self._multiplicador_contradicao = multiplicador_contradicao

    def avaliar(self, analise):
        if analise.tipo is TipoAlegacao.SUBORNO:
            return AvaliacaoJuiz(-20, 1.0, ("O juiz vê a tentativa como afronta ao procedimento.",))
        mod, mult, motivos = 0, 1.0, []
        if analise.evidencias_sustentando:
            mod += self._peso_evidencia * analise.evidencias_sustentando
            motivos.append("O juiz valoriza as provas apresentadas.")
        if analise.classificacao is Classificacao.SEM_EVIDENCIA:
            mod -= self._penalidade_sem_prova
            motivos.append("O juiz rejeita afirmações sem prova descoberta.")
        if analise.classificacao is Classificacao.CONTRADITORIO:
            mod -= 20
            mult = self._multiplicador_contradicao
            motivos.append("O juiz nota a contradição e desconfia mais.")
        if analise.tipo is TipoAlegacao.BLEFE:
            mod -= 10
            motivos.append("O juiz não gosta de blefes.")
        return AvaliacaoJuiz(mod, mult, tuple(motivos))


class JuizPragmatico(Juiz):
    """Helena Duarte: valoriza contexto e testemunhas; técnica sozinha não basta."""

    ID = "pragmatico"

    def __init__(self, nome="Helena Duarte", titulo="Juíza Titular",
                 peso_testemunha=6, limite_bonus_tecnico=12, bonus_alibi=5):
        super().__init__(nome, titulo,
                         "Experiente, observadora e atenta ao contexto humano.",
                         "Direta, perspicaz e humana.")
        self._peso_testemunha = peso_testemunha
        self._limite_bonus_tecnico = limite_bonus_tecnico
        self._bonus_alibi = bonus_alibi

    def avaliar(self, analise):
        if analise.tipo is TipoAlegacao.SUBORNO:
            return AvaliacaoJuiz(-10, 1.0, ("A juíza se ofende, mas pondera o contexto.",))
        mod, mult, motivos = 0, 1.0, []
        tecnico = min(4 * analise.evidencias_sustentando, self._limite_bonus_tecnico)
        if tecnico:
            mod += tecnico
            motivos.append("A juíza considera as provas, mas sem exagerar o peso técnico.")
        if analise.testemunhas_preparadas:
            mod += self._peso_testemunha * analise.testemunhas_preparadas
            motivos.append("Os testemunhos preparados dão contexto à versão.")
        if analise.alibi_preparado:
            mod += self._bonus_alibi
            motivos.append("Um álibi estruturado soa plausível para a juíza.")
        if analise.classificacao is Classificacao.SEM_EVIDENCIA:
            mod -= 10
            motivos.append("A juíza percebe que algo importante foi ignorado.")
        if analise.classificacao is Classificacao.CONTRADITORIO:
            mod -= 15
            mult = 1.2
            motivos.append("A contradição pesa, mas a juíza ouve a explicação.")
        if analise.tipo is TipoAlegacao.BLEFE:
            mod -= 5
        return AvaliacaoJuiz(mod, mult, tuple(motivos))


class JuizCinico(Juiz):
    """Otávio Ferraz: tolera ousadia coerente, castiga blefe frágil."""

    ID = "cinico"

    def __init__(self, nome="Otávio Ferraz", titulo="Juiz Titular",
                 tolerancia_risco=4, penalidade_blefe_fragil=25):
        super().__init__(nome, titulo,
                         "Desconfiado, irônico e difícil de impressionar.",
                         "Sarcástico, incisivo e provocador.")
        self._tolerancia_risco = tolerancia_risco
        self._penalidade_blefe_fragil = penalidade_blefe_fragil

    def avaliar(self, analise):
        if analise.tipo is TipoAlegacao.SUBORNO:
            return AvaliacaoJuiz(-15, 1.0, ("O juiz ri da tentativa, mas anota tudo.",))
        mod, mult, motivos = 0, 1.0, []
        if analise.tipo is TipoAlegacao.BLEFE:
            if analise.classificacao is Classificacao.COERENTE:
                mod += self._tolerancia_risco * analise.nivel_risco
                motivos.append("Ousadia com coerência: o juiz admite que gostou.")
            else:
                mod -= self._penalidade_blefe_fragil
                mult = 2.0 if analise.contradicoes else 1.3
                motivos.append("Um blefe frágil. O juiz nem disfarça o sarcasmo.")
        else:
            mod += 3 * analise.evidencias_sustentando
            if analise.classificacao is Classificacao.CONTRADITORIO:
                mod -= 15
                mult = 1.5
                motivos.append("O juiz aponta a contradição com ironia.")
        return AvaliacaoJuiz(mod, mult, tuple(motivos))


def criar_juiz(id_juiz: str) -> Juiz:
    """Cria o juiz pelo identificador (usado ao carregar partidas salvas e na escolha do jogador)."""
    for classe in (JuizFormalista, JuizPragmatico, JuizCinico):
        if classe.ID == id_juiz:
            return classe()
    raise DadosInvalidosException(f"Juiz desconhecido: {id_juiz}")


def todos_os_juizes() -> list:
    return [JuizFormalista(), JuizPragmatico(), JuizCinico()]
