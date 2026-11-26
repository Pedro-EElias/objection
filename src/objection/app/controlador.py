"""Lógica de jogo da interface, sem nenhum código de tela (por isso é testável).

A tela só chama estes métodos e desenha o que eles devolvem.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from objection.casos.catalogo import obter_caso
from objection.dominio.acao import ArgumentoLivre
from objection.dominio.enums import Classificacao, FasePartida, Permissao, ResultadoVeredito
from objection.dominio.regras import faixa_confianca, nivel_suspeita
from objection.dominio.juiz import criar_juiz
from objection.excecoes import (
    AcaoJaExecutadaException,
    DadosInvalidosException,
    FaseInvalidaException,
    InterpretacaoIndisponivelException,
    ObjectionException,
)
from objection.game.motor_jogo import MotorJogo
from objection.ia.configuracao import ConfiguracaoIA
from objection.ia.contexto import ContextoInterpretacao, ContextoReacao
from objection.ia.dialogo import ServicoDialogo, criar_provedores
from objection.ia.seguranca import MAX_ENTRADA
from objection.persistencia.fabrica import criar_repositorios
from objection.servicos.administracao import ServicoAdministracao
from objection.servicos.autenticacao import ServicoAutenticacao
from objection.servicos.caderno import ServicoCaderno
from objection.servicos.partidas import ServicoPartidas
from objection.servicos.ofertas import ServicoOfertas, garantir_pacotes_padrao
from objection.servicos.tokens import ServicoTokens


class SessaoApp:
    """Reúne repositórios e serviços. Uma por execução do programa."""

    def __init__(self, pasta_dados, relogio=datetime.now, semente=None, config_ia=None, provedores=None):
        self.repos = criar_repositorios(pasta_dados)
        garantir_pacotes_padrao(self.repos)
        self.auth = ServicoAutenticacao(self.repos, relogio=relogio)
        self.tokens = ServicoTokens(self.repos, relogio=relogio)
        self.ofertas = ServicoOfertas(self.repos, self.tokens, relogio=relogio)
        self.administracao = ServicoAdministracao(self.repos, self.tokens, relogio=relogio)
        self.caderno = ServicoCaderno(self.repos, relogio=relogio)
        self.partidas = ServicoPartidas(self.repos)
        self.motor = MotorJogo(semente=semente)
        self.config_ia = config_ia or ConfiguracaoIA.do_ambiente()
        self.provedores = provedores if provedores is not None else criar_provedores(self.config_ia)
        self.dialogo = ServicoDialogo(self.provedores, self.config_ia.cadeias, self.tokens)

    def ia_disponivel(self, id_juiz: str) -> bool:
        """Há algum provedor online configurado para este juiz?"""
        return self.dialogo.tem_ia(id_juiz)

    def partidas_do_jogador(self, usuario) -> list:
        return self.partidas.listar(usuario)


@dataclass(frozen=True)
class OpcaoView:
    id: str
    texto: str
    categoria: str
    custo: int
    risco: str
    estado: str          # "disponivel", "usada" ou "bloqueada"
    motivo: Optional[str] = None


@dataclass(frozen=True)
class TurnoView:
    sucesso: bool
    motivos: tuple
    dialogo: Optional[str]
    objecao: bool
    delta_confianca: int
    delta_suspeita: int
    fase: FasePartida
    fonte: str = "local"
    aviso: Optional[str] = None


@dataclass(frozen=True)
class FimView:
    venceu: bool
    veredito: object
    dialogo: str
    promovido: bool


_AVISOS = {
    "sem_energia": "Energia de IA insuficiente: o juiz falou com frases pré-escritas.",
    "cota_caso": "A cota de IA restante para este caso não cobre a chamada: o juiz falou com frases pré-escritas.",
    "indisponivel": "A IA não respondeu: o juiz falou com frases pré-escritas.",
    "resposta_invalida": "A IA respondeu fora do formato esperado: usei frases pré-escritas.",
}


class ControladorPartida:
    def __init__(self, sessao: SessaoApp, usuario, partida):
        self._sessao = sessao
        self._usuario = usuario
        self._partida = partida
        entrada = obter_caso(partida.id_caso)
        self._caso = entrada.criar_caso()
        self._acoes = {a.id: a for a in entrada.criar_opcoes()}
        self._juiz = criar_juiz(partida.id_juiz)

    # --- criação ---
    @classmethod
    def nova(cls, sessao, usuario, id_caso, id_juiz):
        entrada = obter_caso(id_caso)
        juiz = criar_juiz(id_juiz)
        nome = f"{entrada.titulo} com {juiz.nome}"
        partida = sessao.motor.iniciar_partida(
            entrada.criar_caso(), uuid.uuid4().hex[:10], usuario, id_juiz=id_juiz, nome=nome)
        sessao.repos.partidas.salvar(partida)
        return cls(sessao, usuario, partida)

    @classmethod
    def continuar(cls, sessao, usuario, id_partida):
        partida = sessao.repos.partidas.buscar_por_id(id_partida)
        if partida is None or partida.id_jogador != usuario.id:
            raise DadosInvalidosException("Partida não encontrada.")
        return cls(sessao, usuario, partida)

    # --- leitura ---
    @property
    def partida(self): return self._partida

    @property
    def caso(self): return self._caso

    @property
    def juiz(self): return self._juiz

    @property
    def fase(self): return self._partida.fase

    @property
    def max_rodadas(self): return self._sessao.motor._config.max_rodadas

    def dossie(self) -> list:
        return [e for e in self._caso.evidencias if e.id in self._partida.evidencias_descobertas]

    def historico(self) -> tuple:
        return self._partida.historico

    def opcoes(self) -> list:
        """Opções da fase atual, com o estado de cada uma (disponível, usada, bloqueada)."""
        saida = []
        for acao in self._acoes.values():
            if acao.fase_permitida is not self._partida.fase:
                continue
            estado, motivo = "disponivel", None
            if not self._usuario.pode(acao.permissao_exigida):
                estado, motivo = "bloqueada", "Liberada quando você virar Veterano."
            else:
                try:
                    acao.validar(self._partida, self._caso)
                except AcaoJaExecutadaException:
                    estado, motivo = "usada", "Já feita nesta partida."
                except ObjectionException as erro:
                    estado, motivo = "bloqueada", str(erro)
            saida.append(OpcaoView(acao.id, acao.texto, acao.categoria, acao.custo,
                                   acao.rotulo_risco, estado, motivo))
        return saida

    # --- ações ---
    def _salvar(self):
        self._sessao.repos.partidas.salvar(self._partida)

    def _fatos_publicos(self) -> tuple:
        """Só o que a IA pode saber: fatos do caso e provas já descobertas (nunca as ocultas)."""
        return (*self._caso.fatos_canonicos, *(e.descricao for e in self.dossie()))

    @staticmethod
    def _codigos(acao, resultado) -> tuple:
        if resultado is None:
            return ()
        codigos = []
        classe = resultado.classificacao
        if classe is Classificacao.COERENTE:
            codigos.append("evidencia_relevante")
        elif classe is Classificacao.CONTRADITORIO:
            codigos.append("contradicao_com_provas")
        elif classe is Classificacao.SEM_EVIDENCIA:
            codigos.append("sem_prova_descoberta")
        elif classe is Classificacao.FRACO:
            codigos.append("argumento_fraco")
        if acao.categoria == "blefe":
            codigos.append("blefe_ousado" if resultado.sucesso else "blefe_fragil")
        if acao.categoria == "suborno" and not resultado.sucesso:
            codigos.append("suborno_descoberto")
        return tuple(codigos)

    def _contexto(self, evento, acao=None, resultado=None, indice=None) -> ContextoReacao:
        p = self._partida
        return ContextoReacao(
            evento=evento, indice=len(p.historico) if indice is None else indice, id_caso=p.id_caso,
            texto_alegacao=acao.texto if acao else "",
            classificacao=resultado.classificacao if resultado else None,
            sucesso=resultado.sucesso if resultado else None,
            codigos_motivo=self._codigos(acao, resultado),
            faixa_confianca=faixa_confianca(p.confianca).value, nivel_suspeita=nivel_suspeita(p.suspeita),
            rodada=p.rodada, fatos_publicos=self._fatos_publicos())

    def _dialogar(self, contexto, usar_ia=False):
        return self._sessao.dialogo.gerar(self._usuario, self._partida.id_caso, self._juiz, contexto, usar_ia)

    @staticmethod
    def _evento(acao, resultado) -> Optional[str]:
        if acao.categoria == "suborno":
            return "suborno_ok" if resultado.sucesso else "suborno_descoberto"
        if acao.categoria in ("argumento", "blefe"):
            if resultado.classificacao is Classificacao.CONTRADITORIO:
                return "contradicao"
            if resultado.classificacao is Classificacao.SEM_EVIDENCIA:
                return "sem_evidencia"
            return "convenceu" if resultado.sucesso else "nao_convenceu"
        return None

    def executar(self, id_acao: str, usar_ia: bool = False) -> TurnoView:
        acao = self._acoes.get(id_acao)
        if acao is None:
            raise DadosInvalidosException("Opção inexistente.")
        resultado = self._sessao.motor.executar_acao(
            self._partida, self._caso, self._juiz, acao, self._usuario)
        self._salvar()
        evento = self._evento(acao, resultado)
        dialogo, objecao, fonte, aviso = None, False, "local", None
        if evento:
            r = self._dialogar(self._contexto(evento, acao, resultado), usar_ia)
            dialogo, objecao, fonte = r.reacao.dialogo, r.reacao.objecao, r.provedor
            aviso = _AVISOS.get(r.fallback_motivo)
        return TurnoView(
            resultado.sucesso, resultado.motivos, dialogo, objecao,
            resultado.delta_confianca, resultado.delta_suspeita, self._partida.fase, fonte, aviso)

    def argumento_livre(self, texto: str, usar_ia: bool = True) -> TurnoView:
        """Argumento escrito pelo Veterano. A IA só interpreta (quais afirmações do caso); o motor valida
        e calcula. Sem IA utilizável, nada é alterado."""
        self._usuario.exigir_ativa()
        self._usuario.exigir(Permissao.ARGUMENTO_LIVRE)
        if self._partida.fase is not FasePartida.JULGAMENTO:
            raise FaseInvalidaException("O argumento livre só é possível durante o julgamento.")
        texto = (texto or "").strip()
        if not texto:
            raise DadosInvalidosException("Escreva o seu argumento.")
        if len(texto) > MAX_ENTRADA:
            raise DadosInvalidosException(f"O argumento deve ter até {MAX_ENTRADA} caracteres.")
        catalogo = self._caso.catalogo_afirmacoes
        if not usar_ia:
            raise InterpretacaoIndisponivelException(
                "Ligue o modo \"Juiz com IA (online)\" para argumentar com as suas palavras.")
        if not catalogo:
            raise InterpretacaoIndisponivelException("Este caso ainda não aceita argumentos livres.")
        contexto = ContextoInterpretacao(
            texto=texto, afirmacoes_possiveis=catalogo, id_caso=self._partida.id_caso,
            rodada=self._partida.rodada,
            provas_descobertas=tuple((e.id, e.descricao, e.sustenta) for e in self.dossie()))
        resultado_ia = self._sessao.dialogo.interpretar(
            self._usuario, self._partida.id_caso, self._juiz, contexto)

        if (resultado_ia.conduta_inadequada
                or resultado_ia.interpretacao.conduta_inadequada):  # RN24: manipulação ou gracinha
            self._sessao.motor.registrar_conduta_inadequada(self._partida)
            self._salvar()
            reacao = self._dialogar(self._contexto("conduta_inadequada"), False)
            return TurnoView(False, ("Conduta inadequada: a suspeita do juiz aumentou.",), reacao.reacao.dialogo,
                             True, 0, self._sessao.motor._config.suspeita_conduta_inadequada,
                             self._partida.fase, "local", None)

        interpretacao = resultado_ia.interpretacao
        if not interpretacao.afirmacoes:
            raise DadosInvalidosException(
                "O juiz não reconheceu nenhuma linha de argumento nas suas palavras. "
                "Fale dos fatos ou das provas do caso.")
        acao = ArgumentoLivre(f"livre-{uuid.uuid4().hex[:8]}", texto, interpretacao.afirmacoes,
                              interpretacao.clareza)
        resultado = self._sessao.motor.executar_acao(self._partida, self._caso, self._juiz, acao, self._usuario)
        self._salvar()
        entendido = "Argumento entendido como: " + " ".join(catalogo[a] for a in interpretacao.afirmacoes)
        evento = self._evento(acao, resultado)
        r = self._dialogar(self._contexto(evento, acao, resultado), True)
        return TurnoView(resultado.sucesso, (entendido, *resultado.motivos), r.reacao.dialogo,
                         r.reacao.objecao, resultado.delta_confianca, resultado.delta_suspeita,
                         self._partida.fase, r.provedor, _AVISOS.get(r.fallback_motivo))

    def iniciar_julgamento(self) -> str:
        self._sessao.motor.iniciar_julgamento(self._partida)
        self._salvar()
        return self._dialogar(self._contexto("abertura", indice=0)).reacao.dialogo

    def encerrar(self) -> FimView:
        if self._partida.fase not in (FasePartida.JULGAMENTO, FasePartida.DELIBERACAO):
            raise FaseInvalidaException("O veredito só sai depois do julgamento.")
        veredito = self._sessao.motor.emitir_veredito(self._partida, self._caso)
        venceu = veredito.resultado is ResultadoVeredito.FAVORAVEL
        promovido = self._usuario.registrar_partida_concluida(self._partida.id, venceu)
        self._sessao.repos.usuarios.salvar(self._usuario)
        self._salvar()
        evento = "veredito_favoravel" if venceu else "veredito_desfavoravel"
        return FimView(venceu, veredito, self._dialogar(self._contexto(evento, indice=0)).reacao.dialogo,
                       promovido)

    def abandonar(self):
        self._sessao.motor.abandonar(self._partida)
        self._salvar()
