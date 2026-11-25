"""Lógica de jogo da interface, sem nenhum código de tela (por isso é testável).

A tela só chama estes métodos e desenha o que eles devolvem.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from objection.casos.catalogo import obter_caso
from objection.dominio.enums import Classificacao, FasePartida, ResultadoVeredito
from objection.dominio.juiz import criar_juiz
from objection.excecoes import (
    AcaoJaExecutadaException,
    DadosInvalidosException,
    FaseInvalidaException,
    ObjectionException,
)
from objection.game.motor_jogo import MotorJogo
from objection.ia.local import ProvedorLocal
from objection.persistencia.fabrica import criar_repositorios
from objection.servicos.administracao import ServicoAdministracao
from objection.servicos.autenticacao import ServicoAutenticacao
from objection.servicos.caderno import ServicoCaderno
from objection.servicos.partidas import ServicoPartidas
from objection.servicos.ofertas import ServicoOfertas, garantir_pacotes_padrao
from objection.servicos.tokens import ServicoTokens


class SessaoApp:
    """Reúne repositórios e serviços. Uma por execução do programa."""

    def __init__(self, pasta_dados, relogio=datetime.now, semente=None, provedor=None):
        self.repos = criar_repositorios(pasta_dados)
        garantir_pacotes_padrao(self.repos)
        self.auth = ServicoAutenticacao(self.repos, relogio=relogio)
        self.tokens = ServicoTokens(self.repos, relogio=relogio)
        self.ofertas = ServicoOfertas(self.repos, self.tokens, relogio=relogio)
        self.administracao = ServicoAdministracao(self.repos, self.tokens, relogio=relogio)
        self.caderno = ServicoCaderno(self.repos, relogio=relogio)
        self.partidas = ServicoPartidas(self.repos)
        self.motor = MotorJogo(semente=semente)
        self.provedor = provedor or ProvedorLocal()

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


@dataclass(frozen=True)
class FimView:
    venceu: bool
    veredito: object
    dialogo: str
    promovido: bool


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

    def _reacao(self, evento, indice=None):
        indice = len(self._partida.historico) if indice is None else indice
        return self._sessao.provedor.gerar_reacao(self._juiz, evento, indice)

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

    def executar(self, id_acao: str) -> TurnoView:
        acao = self._acoes.get(id_acao)
        if acao is None:
            raise DadosInvalidosException("Opção inexistente.")
        resultado = self._sessao.motor.executar_acao(
            self._partida, self._caso, self._juiz, acao, self._usuario)
        self._salvar()
        evento = self._evento(acao, resultado)
        reacao = self._reacao(evento) if evento else None
        return TurnoView(
            resultado.sucesso, resultado.motivos,
            reacao.dialogo if reacao else None, bool(reacao and reacao.objecao),
            resultado.delta_confianca, resultado.delta_suspeita, self._partida.fase)

    def iniciar_julgamento(self) -> str:
        self._sessao.motor.iniciar_julgamento(self._partida)
        self._salvar()
        return self._reacao("abertura", 0).dialogo

    def encerrar(self) -> FimView:
        if self._partida.fase not in (FasePartida.JULGAMENTO, FasePartida.DELIBERACAO):
            raise FaseInvalidaException("O veredito só sai depois do julgamento.")
        veredito = self._sessao.motor.emitir_veredito(self._partida, self._caso)
        venceu = veredito.resultado is ResultadoVeredito.FAVORAVEL
        promovido = self._usuario.registrar_partida_concluida(self._partida.id, venceu)
        self._sessao.repos.usuarios.salvar(self._usuario)
        self._salvar()
        evento = "veredito_favoravel" if venceu else "veredito_desfavoravel"
        return FimView(venceu, veredito, self._reacao(evento, 0).dialogo, promovido)

    def abandonar(self):
        self._sessao.motor.abandonar(self._partida)
        self._salvar()
