"""Telas do jogo (Flet). Toda a lógica está em objection.app.controlador."""
import time

import flet as ft

from objection.app.controlador import ControladorPartida
from objection.casos.catalogo import listar_casos, obter_caso
from objection.dominio.enums import FasePartida, ResultadoVeredito
from objection.dominio.juiz import todos_os_juizes
from objection.dominio.usuario import Administrador
from objection.excecoes import ObjectionException
from objection.ui import tema
from objection.ui.componentes import (
    carimbo_objecao, faixa_suspeita, folha, folha_de_evidencia, folha_de_opcao,
    linha_de_historico, medidor, placa_do_juiz, retrato,
)
from objection.ui.tema import botao, texto, titulo

_FASES = {
    FasePartida.PREPARACAO: "Preparação",
    FasePartida.JULGAMENTO: "Julgamento",
    FasePartida.DELIBERACAO: "Aguardando o veredito",
    FasePartida.ENCERRADA: "Encerrada",
    FasePartida.ABANDONADA: "Abandonada",
}


class AppUI:
    def __init__(self, page, sessao, pausa_carimbo=0.9):
        self.page = page
        self.sessao = sessao
        self.pausa_carimbo = pausa_carimbo
        self.usuario = None
        self.ctrl = None
        self.fala = None
        self.narracao = []
        self.carimbo = None

    # ------------------------------------------------------------- base
    def iniciar(self):
        tema.configurar_pagina(self.page)
        self.mostrar_login()

    def _mostrar(self, controle):
        self.page.clean()
        self.page.add(controle)
        self.page.update()

    def _aviso(self, mensagem, erro=False):
        self.page.show_dialog(ft.SnackBar(
            content=texto(mensagem, 16, tema.CREME),
            bgcolor=tema.VINHO_VIVO if erro else tema.CARVAO_2, duration=4000))

    # ------------------------------------------------------------ login
    def mostrar_login(self, modo="entrar"):
        campo_apelido = ft.TextField(
            label="Apelido", autofocus=True, color=tema.TINTA, border_color=tema.TINTA,
            focused_border_color=tema.VINHO, cursor_color=tema.TINTA,
            label_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo"),
            text_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo", size=18))
        campo_senha = ft.TextField(
            label="Senha", password=True, can_reveal_password=True, color=tema.TINTA,
            border_color=tema.TINTA, focused_border_color=tema.VINHO, cursor_color=tema.TINTA,
            label_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo"),
            text_style=ft.TextStyle(color=tema.TINTA, font_family="Corpo", size=18))
        mensagem = texto("", 15, tema.VINHO_VIVO, "CorpoMedio")

        def enviar(e=None):
            try:
                if modo == "entrar":
                    self.entrar(campo_apelido.value, campo_senha.value)
                else:
                    self.cadastrar(campo_apelido.value, campo_senha.value)
            except ObjectionException as erro:
                mensagem.value = str(erro)
                self.page.update()

        campo_senha.on_submit = enviar
        alternar = botao("Criar conta" if modo == "entrar" else "Já tenho conta",
                         lambda e: self.mostrar_login("cadastro" if modo == "entrar" else "entrar"),
                         "secundario")
        formulario = folha(ft.Column([
            texto("Entrar na sala" if modo == "entrar" else "Criar uma conta de jogador", 24, tema.TINTA, "Fell"),
            campo_apelido, campo_senha, mensagem,
            ft.Row([botao("Entrar" if modo == "entrar" else "Criar conta e entrar", enviar), alternar],
                   spacing=12, wrap=True),
        ], spacing=14), largura=420, padding=26)
        apresentacao = ft.Column([
            titulo("OBJECTION!", 96),
            texto("The Art of Deception", 32, tema.LATAO, "FellItalico"),
            ft.Container(height=18),
            texto("Você defende o réu diante de um juiz que não se deixa enganar com facilidade.",
                  20, tema.CREME),
            texto("Cada argumento, blefe e prova muda o que o juiz pensa de você.",
                  20, tema.CREME_APAGADO),
        ], spacing=4, expand=True, alignment=ft.MainAxisAlignment.CENTER)
        self._mostrar(ft.Container(
            content=ft.Row([apresentacao, formulario], spacing=60,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=70, vertical=40), expand=True))

    def entrar(self, apelido, senha):
        self.usuario = self.sessao.auth.login(apelido, senha)
        self.mostrar_home()

    def cadastrar(self, apelido, senha):
        self.sessao.auth.cadastrar_jogador(apelido, senha)
        self.entrar(apelido, senha)

    def sair(self):
        self.usuario, self.ctrl, self.fala, self.narracao = None, None, None, []
        self.mostrar_login()

    # ------------------------------------------------------------- início
    def mostrar_home(self):
        self.ctrl = None
        if isinstance(self.usuario, Administrador):
            return self._home_admin()
        self._home_jogador()

    def _barra_topo(self, extras=()):
        return ft.Row([
            ft.Column([titulo("OBJECTION!", 34),
                       texto(f"{self.usuario.apelido}, {self._perfil_texto()}", 16, tema.CREME_APAGADO)],
                      spacing=0, expand=True),
            *extras,
            botao("Sair", lambda e: self.sair(), "secundario"),
        ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _perfil_texto(self):
        if isinstance(self.usuario, Administrador):
            return "administrador"
        return "jogador novato" if self.usuario.nivel.value == "novato" else "jogador veterano"

    def _home_jogador(self):
        energia = self.sessao.tokens.energia(self.usuario)
        casos = []
        for entrada in listar_casos():
            casos.append(folha(ft.Column([
                texto(entrada.titulo, 26, tema.TINTA, "Fell"),
                texto(entrada.sinopse, 17, tema.TINTA),
                botao("Novo julgamento", lambda e, i=entrada.id: self.mostrar_intro_caso(i)),
            ], spacing=10), faixa_cor=tema.LATAO, padding=18))
        for titulo_futuro in ("O Contrato Fantasma", "A Noite do Incêndio"):
            casos.append(folha(ft.Column([
                texto(titulo_futuro, 22, "#6B6459", "Fell"),
                texto("Ainda não disponível.", 16, "#6B6459", "CorpoItalico"),
            ], spacing=2), faixa_cor=tema.PAPEL_ESCURO, padding=14))

        salvas = []
        for p in self.sessao.partidas_do_jogador(self.usuario):
            ativa = p.fase in (FasePartida.PREPARACAO, FasePartida.JULGAMENTO, FasePartida.DELIBERACAO)
            situacao = _FASES[p.fase]
            if p.veredito:
                situacao = ("Encerrada, veredito favorável" if p.veredito.resultado is
                            ResultadoVeredito.FAVORAVEL else "Encerrada, veredito desfavorável")
            salvas.append(ft.Row([
                ft.Column([texto(p.nome, 17, tema.CREME, "CorpoMedio"),
                           texto(situacao, 15, tema.CREME_APAGADO, "CorpoItalico")], spacing=0, expand=True),
                botao("Continuar", lambda e, i=p.id: self.continuar_partida(i), "secundario") if ativa
                else ft.Container(),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
        if not salvas:
            salvas.append(texto("Nenhuma partida ainda. Escolha um caso para começar.", 17,
                                tema.CREME_APAGADO, "CorpoItalico"))

        energia_bloco = ft.Container(
            content=medidor("Energia de IA", energia, 100, tema.LATAO, "de 100"), width=260)
        self._mostrar(ft.Container(content=ft.Column([
            self._barra_topo([energia_bloco, botao("Ofertas", lambda e: self.mostrar_ofertas(), "secundario")]),
            ft.Container(height=14),
            ft.ResponsiveRow([
                ft.Column([titulo("Casos", 28), *casos], col={"xs": 12, "md": 7}, spacing=14),
                ft.Column([titulo("Partidas salvas", 28), *salvas], col={"xs": 12, "md": 5}, spacing=14),
            ], spacing=30, run_spacing=30),
        ], scroll=ft.ScrollMode.AUTO, spacing=10), padding=36, expand=True))

    def _home_admin(self):
        resumo = self.sessao.administracao.resumo_consumo(self.usuario)
        linhas = [texto(f"Total de tokens usados: {resumo['total']} "
                        f"(reais {resumo['real']}, simulados {resumo['simulado']}).", 18)]
        for conta, qtd in resumo["por_conta"].items():
            linhas.append(texto(f"{conta}: {qtd} tokens", 17, tema.CREME_APAGADO))
        if not resumo["por_conta"]:
            linhas.append(texto("Ainda não há consumo registrado.", 17, tema.CREME_APAGADO, "CorpoItalico"))
        self._mostrar(ft.Container(content=ft.Column([
            self._barra_topo(),
            ft.Container(height=14),
            titulo("Painel do administrador", 30),
            texto("A gestão de contas, cotas e pacotes chega na próxima etapa. Por enquanto, o consumo:",
                  17, tema.CREME_APAGADO),
            *linhas,
        ], spacing=10, scroll=ft.ScrollMode.AUTO), padding=36, expand=True))

    # ----------------------------------------------------------- ofertas
    def mostrar_ofertas(self):
        carteira = self.sessao.tokens.carteira_atual(self.usuario.id)
        disponiveis = self.sessao.ofertas.listar_disponiveis(self.usuario)
        itens = []
        for p in disponiveis:
            pct = round(100 * p.tokens / max(1, carteira.cota_diaria))
            itens.append(ft.Row([
                ft.Column([texto(p.nome, 18, tema.TINTA, "CorpoMedio"),
                           texto(f"Recarrega cerca de {pct}% da energia.", 15, tema.TINTA, "CorpoItalico")],
                          spacing=0, expand=True),
                botao("Resgatar", lambda e, i=p.id: self.resgatar(i), "papel"),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
        if not itens:
            itens.append(texto("Nenhuma oferta disponível agora. Volte amanhã.", 17, tema.TINTA, "CorpoItalico"))
        self.page.show_dialog(ft.AlertDialog(
            bgcolor=tema.PAPEL, title=texto("Ofertas", 28, tema.TINTA, "Fell"),
            content=ft.Container(ft.Column(itens, spacing=14, tight=True), width=460),
            actions=[botao("Fechar", lambda e: self.page.pop_dialog(), "secundario")]))

    def resgatar(self, id_pacote):
        try:
            self.sessao.ofertas.resgatar(self.usuario, id_pacote)
        except ObjectionException as erro:
            self._aviso(str(erro), erro=True)
            return
        self.page.pop_dialog()
        self.mostrar_home()
        self._aviso("Oferta resgatada. Sua energia foi recarregada.")

    # -------------------------------------------------------- escolha do juiz
    def mostrar_intro_caso(self, id_caso):
        entrada = obter_caso(id_caso)
        caso = entrada.criar_caso()
        fatos = ft.Column([texto(f, 17, tema.TINTA) for f in caso.fatos_canonicos], spacing=4)
        cartoes = []
        for j in todos_os_juizes():
            cartoes.append(ft.Column([
                retrato(j, 110), placa_do_juiz(j),
                texto(j.perfil, 15, tema.CREME_APAGADO),
                texto(f"Fala de modo {j.estilo_fala[:1].lower() + j.estilo_fala[1:]}", 15, tema.CREME_APAGADO,
                      "CorpoItalico"),
                botao("Escolher este juiz", lambda e, i=j.id: self.iniciar_partida(id_caso, i)),
            ], spacing=8, col={"xs": 12, "md": 4}))
        self._mostrar(ft.Container(content=ft.Column([
            ft.Row([botao("Voltar", lambda e: self.mostrar_home(), "secundario")]),
            titulo(caso.titulo, 44),
            texto(caso.acusacao, 20, tema.LATAO, "FellItalico"),
            folha(fatos, faixa_cor=tema.LATAO, padding=16),
            ft.Container(height=8),
            titulo("Quem vai julgar?", 30),
            texto("Cada juiz pesa as provas, os blefes e as contradições de um jeito diferente.", 17,
                  tema.CREME_APAGADO),
            ft.ResponsiveRow(cartoes, spacing=24, run_spacing=24),
        ], spacing=12, scroll=ft.ScrollMode.AUTO), padding=36, expand=True))

    def iniciar_partida(self, id_caso, id_juiz):
        try:
            self.ctrl = ControladorPartida.nova(self.sessao, self.usuario, id_caso, id_juiz)
        except ObjectionException as erro:
            self._aviso(str(erro), erro=True)
            return
        self.fala, self.narracao = None, []
        self.mostrar_partida()

    def continuar_partida(self, id_partida):
        try:
            self.ctrl = ControladorPartida.continuar(self.sessao, self.usuario, id_partida)
        except ObjectionException as erro:
            self._aviso(str(erro), erro=True)
            return
        self.fala, self.narracao = None, []
        self.mostrar_partida()

    # ---------------------------------------------------------------- partida
    def mostrar_partida(self):
        c = self.ctrl
        p = c.partida
        fase = c.fase
        if fase is FasePartida.JULGAMENTO:
            situacao = f"Julgamento, rodada {p.rodada} de {c.max_rodadas}"
        else:
            situacao = _FASES[fase]

        if fase is FasePartida.PREPARACAO:
            acao_principal = botao("Ir ao julgamento", lambda e: self.ir_ao_julgamento())
        elif fase is FasePartida.JULGAMENTO:
            acao_principal = botao("Encerrar e ouvir o veredito", lambda e: self.encerrar(), "secundario")
        else:
            acao_principal = botao("Ouvir o veredito", lambda e: self.encerrar())

        topo = ft.Row([
            ft.Column([titulo(c.caso.titulo, 30), texto(situacao, 17, tema.LATAO, "CorpoMedio")],
                      spacing=0, expand=True),
            acao_principal,
            botao("Sair da partida", lambda e: self._sair_da_partida(), "secundario"),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        coluna_juiz = ft.Column([
            retrato(c.juiz, 150), placa_do_juiz(c.juiz), ft.Container(height=6),
            medidor("Confiança", p.confianca, 100, tema.LATAO, self._faixa_confianca_texto(p.confianca)),
            medidor("Suspeita", p.suspeita, 100, tema.VINHO_VIVO, faixa_suspeita(p.suspeita)),
            medidor("Créditos", p.orcamento, self.sessao.motor._config.orcamento_inicial, tema.CREME_APAGADO,
                    "de 100"),
        ], spacing=12, col={"xs": 12, "md": 3})

        if self.fala:
            palco = ft.Container(
                content=ft.Column([
                    texto(f"{c.juiz.nome} diz:", 16, tema.LATAO, "CorpoMedio"),
                    texto(f"“{self.fala}”", 28, tema.CREME, "FellItalico"),
                ], spacing=6),
                border=ft.Border.only(left=ft.BorderSide(3, tema.LATAO)),
                padding=ft.Padding.only(left=18, top=4, bottom=4))
        else:
            dica = ("Reúna provas antes de entrar em julgamento. Cada ação custa créditos."
                    if fase is FasePartida.PREPARACAO else "O julgamento chegou ao fim.")
            palco = texto(dica, 20, tema.CREME_APAGADO, "CorpoItalico")
        narracao = [texto(m, 16, tema.CREME_APAGADO) for m in self.narracao]

        opcoes = [folha_de_opcao(o, self.usar_opcao) for o in c.opcoes()]
        if fase is FasePartida.DELIBERACAO:
            opcoes = [texto("Não restam rodadas ou o juiz já viu o bastante. Peça o veredito.", 18,
                            tema.CREME)]
        coluna_centro = ft.Column([
            palco, *narracao, ft.Container(height=6),
            titulo("Suas opções" if opcoes else "", 26), *opcoes,
        ], spacing=10, col={"xs": 12, "md": 6})

        dossie = [folha_de_evidencia(e) for e in c.dossie()] or [
            texto("Nenhuma prova descoberta ainda.", 16, tema.CREME_APAGADO, "CorpoItalico")]
        historico = [linha_de_historico(e) for e in c.historico()] or [
            texto("Ainda sem ações.", 16, tema.CREME_APAGADO, "CorpoItalico")]
        coluna_autos = ft.Column([
            titulo("Dossiê", 26), *dossie, ft.Container(height=6),
            titulo("Histórico", 26), *historico,
        ], spacing=10, col={"xs": 12, "md": 3})

        self.carimbo = carimbo_objecao()
        conteudo = ft.Container(content=ft.Column([
            topo, ft.Container(height=8),
            ft.ResponsiveRow([coluna_juiz, coluna_centro, coluna_autos], spacing=28, run_spacing=24),
        ], scroll=ft.ScrollMode.AUTO, spacing=10), padding=32, expand=True)
        self._mostrar(ft.Stack([conteudo, self.carimbo], expand=True))

    @staticmethod
    def _faixa_confianca_texto(valor):
        from objection.dominio.regras import faixa_confianca
        return faixa_confianca(valor).value

    def usar_opcao(self, id_acao):
        try:
            turno = self.ctrl.executar(id_acao)
        except ObjectionException as erro:
            self._aviso(str(erro), erro=True)
            self.mostrar_partida()
            return
        self.narracao = list(turno.motivos)
        if turno.dialogo:
            self.fala = turno.dialogo
        self.mostrar_partida()
        if turno.objecao:
            self._animar_objecao()

    def _animar_objecao(self):
        self.carimbo.opacity = 1
        self.carimbo.scale = 1
        self.page.update()
        time.sleep(self.pausa_carimbo)
        self.carimbo.opacity = 0
        self.page.update()

    def ir_ao_julgamento(self):
        try:
            self.fala = self.ctrl.iniciar_julgamento()
        except ObjectionException as erro:
            self._aviso(str(erro), erro=True)
            return
        self.narracao = []
        self.mostrar_partida()

    def _sair_da_partida(self):
        self.mostrar_home()
        self._aviso("Partida salva. Você pode continuar de onde parou.")

    # ---------------------------------------------------------------- veredito
    def encerrar(self):
        try:
            fim = self.ctrl.encerrar()
        except ObjectionException as erro:
            self._aviso(str(erro), erro=True)
            return
        self.mostrar_veredito(fim)

    def mostrar_veredito(self, fim):
        c, v = self.ctrl, fim.veredito
        cabecalho = "Veredito favorável: réu absolvido" if fim.venceu else "Veredito desfavorável: réu condenado"
        eventos = []
        for e in c.historico():
            eventos.append(folha(ft.Column([
                texto(e.descricao, 17, tema.TINTA, "CorpoMedio"),
                texto(("Funcionou. " if e.sucesso else "Não funcionou. ") + " ".join(e.motivos[-2:]),
                      15, tema.TINTA, "CorpoItalico"),
            ], spacing=2), faixa_cor=tema.VERDE_AUTOS if e.sucesso else tema.VINHO_VIVO, padding=12))
        promocao = [texto("Você virou jogador veterano: blefes e suborno estão liberados.", 20, tema.LATAO,
                          "CorpoNegrito")] if fim.promovido else []
        self._mostrar(ft.Container(content=ft.Column([
            titulo(cabecalho, 44),
            ft.Container(
                content=texto(f"“{fim.dialogo}”", 28, tema.CREME, "FellItalico"),
                border=ft.Border.only(left=ft.BorderSide(3, tema.LATAO)),
                padding=ft.Padding.only(left=18, top=4, bottom=4)),
            texto(f"{c.juiz.nome}, {c.juiz.titulo.lower()}.", 16, tema.CREME_APAGADO),
            texto(f"Confiança final {v.confianca_final} ({v.faixa.value}). "
                  f"Suspeita final {v.suspeita_final}. Créditos restantes {c.partida.orcamento}.", 18),
            *promocao,
            titulo("Como suas decisões levaram a este resultado", 26),
            *(eventos or [texto("Você foi direto ao veredito, sem nenhuma ação.", 17, tema.CREME_APAGADO,
                                "CorpoItalico")]),
            ft.Row([botao("Voltar ao início", lambda e: self.mostrar_home())]),
        ], spacing=14, scroll=ft.ScrollMode.AUTO), padding=40, expand=True))
