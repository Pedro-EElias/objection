import pytest

from objection.app.controlador import ControladorPartida, SessaoApp
from objection.casos.catalogo import listar_casos, obter_caso
from objection.dominio.acao import Investigacao, PrepararTestemunha
from objection.dominio.enums import FasePartida, NivelJogador
from objection.dominio.juiz import todos_os_juizes
from objection.excecoes import AcessoNegadoException, DadosInvalidosException, FaseInvalidaException
from objection.ia.contexto import ContextoReacao
from objection.ia.local import _FALAS, ProvedorLocal


@pytest.fixture
def sessao(tmp_path, relogio):
    return SessaoApp(tmp_path, relogio=relogio, semente=3)


@pytest.fixture
def auth(sessao):
    return sessao.auth  # no app real há uma única sessão (e portanto um único repositório por arquivo)


@pytest.fixture
def jogador(sessao):
    return sessao.auth.cadastrar_jogador("ana", "Senha@123")


@pytest.fixture
def ctrl(sessao, jogador):
    return ControladorPartida.nova(sessao, jogador, "caso-1", "formalista")


# ----------------------------------------------------------------- catálogo
def test_opcoes_do_caso_1_sao_consistentes():
    entrada = obter_caso("caso-1")
    caso, opcoes = entrada.criar_caso(), entrada.criar_opcoes()
    ids = [o.id for o in opcoes]
    assert len(ids) == len(set(ids))
    for o in opcoes:
        if isinstance(o, Investigacao):
            caso.evidencia(o.id_evidencia)
        if isinstance(o, PrepararTestemunha):
            assert caso.tem_testemunha(o.id_testemunha)
        for ev in getattr(o, "evidencias_citadas", ()):
            caso.evidencia(ev)


def test_todo_juiz_tem_fala_para_todo_evento():
    eventos = set(_FALAS["formalista"])
    for juiz in todos_os_juizes():
        assert set(_FALAS[juiz.id]) == eventos
        for evento in eventos:
            assert ProvedorLocal().gerar_reacao(juiz, ContextoReacao(evento=evento)).dialogo


def test_catalogo_lista_o_caso_1():
    assert [c.id for c in listar_casos()] == ["caso-1"]


# --------------------------------------------------------------- fluxo
def test_nova_partida_e_salva_e_pode_ser_continuada(sessao, jogador, tmp_path, relogio):
    c = ControladorPartida.nova(sessao, jogador, "caso-1", "pragmatico")
    c.executar("i-catraca")
    outra = SessaoApp(tmp_path, relogio=relogio)  # "reabrir o programa"
    usuario = outra.repos.usuarios.buscar_por_id(jogador.id)
    de_novo = ControladorPartida.continuar(outra, usuario, c.partida.id)
    assert de_novo.partida.orcamento == 80
    assert [e.id for e in de_novo.dossie()] == ["E1"]
    assert de_novo.juiz.id == "pragmatico"


def test_nao_continua_partida_de_outro_jogador(sessao, ctrl, auth):
    outro = auth.cadastrar_jogador("bia", "Senha@123")
    with pytest.raises(DadosInvalidosException):
        ControladorPartida.continuar(sessao, outro, ctrl.partida.id)


def test_opcoes_da_preparacao_e_seus_estados(ctrl):
    opcoes = {o.id: o for o in ctrl.opcoes()}
    assert "ar-saida" not in opcoes  # argumento só no julgamento
    assert opcoes["i-catraca"].estado == "disponivel" and opcoes["i-catraca"].custo == 20
    ctrl.executar("i-catraca")
    assert {o.id: o for o in ctrl.opcoes()}["i-catraca"].estado == "usada"


def test_opcao_fica_bloqueada_sem_creditos(ctrl):
    for acao in ("i-catraca", "i-pericia", "i-corredor", "t-corredor"):
        ctrl.executar(acao)  # 20 + 20 + 20 + 15 = 75
    opcoes = {o.id: o for o in ctrl.opcoes()}
    assert opcoes["al-casa"].estado == "bloqueada"
    assert "insuficiente" in opcoes["al-casa"].motivo.lower()


def test_novato_ve_blefe_bloqueado_e_suborno_bloqueado(ctrl):
    assert {o.id: o for o in ctrl.opcoes()}["su-discreto"].estado == "bloqueada"
    ctrl.iniciar_julgamento()
    opcoes = {o.id: o for o in ctrl.opcoes()}
    assert opcoes["bl-seguranca"].estado == "bloqueada" and "Veterano" in opcoes["bl-seguranca"].motivo
    assert opcoes["ar-saida"].estado == "disponivel"
    with pytest.raises(AcessoNegadoException):
        ctrl.executar("bl-seguranca")


def test_executar_opcao_inexistente(ctrl):
    with pytest.raises(DadosInvalidosException):
        ctrl.executar("nao-existe")


def test_veredito_so_depois_do_julgamento(ctrl):
    with pytest.raises(FaseInvalidaException):
        ctrl.encerrar()


def test_contradicao_gera_objecao_na_resposta(ctrl):
    ctrl.executar("i-mensagens")  # revela E4, que refuta "saiu antes do fechamento"
    ctrl.iniciar_julgamento()
    turno = ctrl.executar("ar-saida")
    assert turno.objecao is True and turno.dialogo


def test_partida_completa_e_persistida_e_conta_para_o_jogador(sessao, ctrl, jogador):
    for acao in ("i-catraca", "i-pericia", "i-corredor"):
        ctrl.executar(acao)
    abertura = ctrl.iniciar_julgamento()
    assert abertura
    for acao in ("ar-saida", "ar-chave", "ar-corredor"):
        if ctrl.fase is FasePartida.JULGAMENTO:
            ctrl.executar(acao)
    fim = ctrl.encerrar()
    assert fim.dialogo and ctrl.fase is FasePartida.ENCERRADA
    salvo = sessao.repos.partidas.buscar_por_id(ctrl.partida.id)
    assert salvo.veredito is not None
    assert ctrl.partida.id in sessao.repos.usuarios.buscar_por_id(jogador.id).partidas_concluidas


def test_promocao_aparece_no_fim_da_partida(sessao, jogador):
    jogador.registrar_partida_concluida("a", True)
    jogador.registrar_partida_concluida("b", True)
    c = ControladorPartida.nova(sessao, jogador, "caso-1", "cinico")
    c.iniciar_julgamento()
    fim = c.encerrar()
    assert fim.promovido is True and jogador.nivel is NivelJogador.VETERANO


def test_partidas_do_jogador(sessao, jogador, auth):
    outro = auth.cadastrar_jogador("bia", "Senha@123")
    ControladorPartida.nova(sessao, jogador, "caso-1", "formalista")
    ControladorPartida.nova(sessao, outro, "caso-1", "cinico")
    assert len(sessao.partidas_do_jogador(jogador)) == 1


def test_abandonar_partida(ctrl):
    ctrl.abandonar()
    assert ctrl.fase is FasePartida.ABANDONADA


# -------------------------------------------------------- balanceamento
def _taxa_de_vitoria(tmp_path_factory, plano_prep, plano_julg, id_juiz, n=40):
    vitorias = 0
    for semente in range(n):
        pasta = tmp_path_factory.mktemp("bal")
        s = SessaoApp(pasta, semente=semente)
        u = s.auth.cadastrar_jogador(f"jog{semente}", "Senha@123")
        c = ControladorPartida.nova(s, u, "caso-1", id_juiz)
        for a in plano_prep:
            c.executar(a)
        c.iniciar_julgamento()
        for a in plano_julg:
            if c.fase is FasePartida.JULGAMENTO:
                c.executar(a)
        vitorias += c.encerrar().venceu
    return vitorias / n


@pytest.mark.parametrize("id_juiz", ["formalista", "pragmatico", "cinico"])
def test_jogar_bem_ganha_mais_que_jogar_mal(tmp_path_factory, id_juiz):
    bom = _taxa_de_vitoria(tmp_path_factory, ["i-catraca", "i-pericia", "i-corredor", "t-corredor"],
                           ["ar-saida", "ar-chave", "ar-corredor"], id_juiz)
    fraco = _taxa_de_vitoria(tmp_path_factory, [], ["ar-carater", "ar-oficio", "ar-saida"], id_juiz)
    assert 0.5 <= bom <= 0.95
    assert fraco <= 0.15 and bom > fraco
