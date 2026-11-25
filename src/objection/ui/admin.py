"""Painel do administrador: consumo, contas e pacotes."""
import flet as ft

from objection.app.painel_admin import ler_data, ler_inteiro, linhas_de_contas
from objection.ui import tema
from objection.ui.componentes import folha
from objection.ui.dialogos import campo, dialogo_confirmacao, dialogo_formulario, interruptor
from objection.ui.tema import botao, texto, titulo

SECOES = (("consumo", "Consumo"), ("contas", "Contas"), ("pacotes", "Pacotes"))


def tela_admin(app) -> ft.Control:
    nav = ft.Row([
        botao(rotulo, lambda e, i=id_: _trocar(app, i), "principal" if app.secao_admin == id_ else "secundario")
        for id_, rotulo in SECOES], spacing=10, wrap=True)
    corpo = {"consumo": _consumo, "contas": _contas, "pacotes": _pacotes}[app.secao_admin](app)
    return ft.Container(content=ft.Column([
        app._barra_topo(), ft.Container(height=10),
        titulo("Painel do administrador", 32), nav, ft.Container(height=6), *corpo,
    ], spacing=12, scroll=ft.ScrollMode.AUTO), padding=36, expand=True)


def _trocar(app, secao):
    app.secao_admin = secao
    app.mostrar_home()


# --------------------------------------------------------------- consumo
def _consumo(app) -> list:
    r = app.sessao.administracao.resumo_consumo(app.usuario)
    blocos = [texto(f"Total de tokens usados: {r['total']}. Reais: {r['real']}. Simulados: {r['simulado']}.", 19)]
    if not r["total"]:
        blocos.append(texto("Ainda não há consumo registrado.", 17, tema.CREME_APAGADO, "CorpoItalico"))
    for rotulo, chave in (("Por conta", "por_conta"), ("Por caso", "por_caso"),
                          ("Por juiz", "por_juiz"), ("Por provedor", "por_provedor")):
        if r[chave]:
            blocos.append(titulo(rotulo, 24))
            for nome, qtd in sorted(r[chave].items(), key=lambda par: -par[1]):
                blocos.append(texto(f"{nome}: {qtd} tokens", 17, tema.CREME_APAGADO))
    return blocos


# ---------------------------------------------------------------- contas
def _contas(app) -> list:
    linhas = linhas_de_contas(app.sessao, app.usuario)
    if not linhas:
        return [texto("Nenhum jogador cadastrado ainda.", 17, tema.CREME_APAGADO, "CorpoItalico")]
    saida = []
    for c in linhas:
        suspensa = c.status == "suspensa"
        saida.append(folha(ft.Column([
            ft.Row([titulo_papel(f"{c.apelido}"), texto(f"{c.nivel}, conta {c.status}", 16, tema.TINTA,
                                                         "CorpoItalico")], spacing=12),
            texto(f"Energia {c.energia}%. Saldo {c.saldo} tokens, cota diária {c.cota_diaria}, "
                  f"cota por caso {c.cota_por_caso}. {c.partidas} partidas concluídas, "
                  f"{c.vitorias} vitórias.", 16, tema.TINTA),
            ft.Row([
                botao("Cotas e tokens", lambda e, c=c: _dialogo_cotas(app, c), "papel"),
                botao("Reativar" if suspensa else "Suspender",
                      lambda e, c=c, s=suspensa: _alternar_suspensao(app, c, s), "papel"),
                botao("Remover", lambda e, c=c: _remover_conta(app, c), "perigo"),
            ], spacing=10, wrap=True),
        ], spacing=8), faixa_cor=tema.VINHO_VIVO if suspensa else tema.LATAO, padding=16))
    return saida


def titulo_papel(valor):
    return texto(valor, 22, tema.TINTA, "Fell")


def _dialogo_cotas(app, c):
    cota_dia = campo("Cota diária (tokens)", str(c.cota_diaria))
    cota_caso = campo("Cota por caso (tokens)", str(c.cota_por_caso))
    conceder = campo("Conceder tokens (opcional)")
    revogar = campo("Revogar tokens (opcional)")

    def salvar():
        adm, admin = app.sessao.administracao, app.usuario
        nova_dia = ler_inteiro(cota_dia.value, "A cota diária")
        nova_caso = ler_inteiro(cota_caso.value, "A cota por caso")
        dar = ler_inteiro(conceder.value, "O valor a conceder", opcional=True)
        tirar = ler_inteiro(revogar.value, "O valor a revogar", opcional=True)
        if nova_dia != c.cota_diaria:
            adm.definir_cota_diaria(admin, c.id, nova_dia)
        if nova_caso != c.cota_por_caso:
            adm.definir_cota_por_caso(admin, c.id, nova_caso)
        if dar:
            adm.conceder_tokens(admin, c.id, dar)
        if tirar:
            adm.revogar_tokens(admin, c.id, tirar)

    dialogo_formulario(app, f"Cotas de {c.apelido}", [cota_dia, cota_caso, conceder, revogar],
                       salvar, app.mostrar_home)


def _alternar_suspensao(app, c, suspensa):
    adm = app.sessao.administracao
    (adm.reativar_conta if suspensa else adm.suspender_conta)(app.usuario, c.id)
    app.mostrar_home()


def _remover_conta(app, c):
    def remover():
        app.sessao.administracao.remover_conta(app.usuario, c.id)
        app.mostrar_home()

    dialogo_confirmacao(app, "Remover conta",
                        f"A conta de {c.apelido}, as partidas e as anotações serão apagadas. "
                        "O histórico de consumo é mantido. Isso não pode ser desfeito.", remover, "Remover")


# --------------------------------------------------------------- pacotes
def _pacotes(app) -> list:
    pacotes = app.sessao.administracao.listar_pacotes(app.usuario)
    saida = [botao("Novo pacote", lambda e: _dialogo_pacote(app))]
    for p in pacotes:
        regras = []
        regras.append("uma vez por dia" if p.uma_por_dia else "")
        regras.append(f"até {p.limite_por_conta} por conta" if p.limite_por_conta else "sem limite por conta")
        regras.append(f"válido até {p.validade_ate.isoformat()}" if p.validade_ate else "sem validade")
        regras.append("ativo" if p.ativo else "desativado")
        saida.append(folha(ft.Column([
            ft.Row([titulo_papel(p.nome), texto(f"{p.tokens} tokens", 16, tema.TINTA, "CorpoItalico")], spacing=12),
            texto(", ".join(r for r in regras if r) + ".", 16, tema.TINTA),
            ft.Row([botao("Editar", lambda e, p=p: _dialogo_pacote(app, p), "papel"),
                    botao("Remover", lambda e, p=p: _remover_pacote(app, p), "perigo")], spacing=10),
        ], spacing=8), faixa_cor=tema.LATAO if p.ativo else tema.PAPEL_ESCURO, padding=16))
    return saida


def _dialogo_pacote(app, pacote=None):
    nome = campo("Nome", pacote.nome if pacote else "")
    tokens = campo("Tokens concedidos", str(pacote.tokens) if pacote else "")
    limite = campo("Limite de resgates por conta (vazio = sem limite)",
                   str(pacote.limite_por_conta) if pacote and pacote.limite_por_conta else "")
    validade = campo("Válido até, AAAA-MM-DD (vazio = sem validade)",
                     pacote.validade_ate.isoformat() if pacote and pacote.validade_ate else "")
    por_dia = interruptor("Só um resgate por dia", bool(pacote and pacote.uma_por_dia))
    ativo = interruptor("Pacote ativo", True if pacote is None else pacote.ativo)

    def salvar():
        adm = app.sessao.administracao
        dados = dict(
            limite_por_conta=ler_inteiro(limite.value, "O limite", opcional=True, minimo=1),
            uma_por_dia=por_dia.value, validade_ate=ler_data(validade.value, "A validade"),
            ativo=ativo.value)
        qtd = ler_inteiro(tokens.value, "Os tokens", minimo=1)
        if pacote is None:
            adm.criar_pacote(app.usuario, nome.value, qtd, **dados)
        else:
            adm.alterar_pacote(app.usuario, pacote.id, nome=nome.value, tokens=qtd, **dados)

    dialogo_formulario(app, "Editar pacote" if pacote else "Novo pacote",
                       [nome, tokens, limite, validade, por_dia, ativo], salvar, app.mostrar_home)


def _remover_pacote(app, p):
    def remover():
        app.sessao.administracao.remover_pacote(app.usuario, p.id)
        app.mostrar_home()

    dialogo_confirmacao(app, "Remover pacote", f"O pacote “{p.nome}” será removido.", remover, "Remover")
