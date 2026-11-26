"""Telas do jogo (Flet). Toda a lógica está em objection.app.controlador."""
import time

import flet as ft

from objection.app.controlador import ControladorPartida
from objection.casos.catalogo import listar_casos, obter_caso
from objection.dominio.enums import FasePartida, Permissao, ResultadoVeredito
from objection.dominio.juiz import todos_os_juizes
from objection.dominio.usuario import Administrador
from objection.excecoes import ObjectionException
from objection.ui import tema
from objection.ui.admin import tela_admin
from objection.ui.dialogos import caixa, campo, dialogo_confirmacao, dialogo_formulario
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
        self.secao_admin = "consumo"
        self.usar_ia = False
        self.ocupado = False
        self.carregando = False
        self.fonte_fala = "local"
        self.aviso_ia = None

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
        dica_senha = [] if modo == "entrar" else [texto(
            "Use 8 ou mais caracteres, com letra maiúscula, minúscula, número e caractere especial.",
            14, tema.TINTA, "CorpoItalico")]
        formulario = folha(ft.Column([
            texto("Entrar na sala" if modo == "entrar" else "Criar uma conta de jogador", 24, tema.TINTA, "Fell"),
            campo_apelido, campo_senha, *dica_senha, mensagem,
            ft.Row([botao("Entrar" if modo == "entrar" else "Criar conta e entrar", enviar), alternar],
                   spacing=12, wrap=True),
        ], spacing=14), largura=420, padding=26)
        # O título nunca quebra: o tamanho acompanha o espaço que sobra ao lado do formulário.
        largura_pagina = getattr(self.page, "width", None) or 1160
        largura_texto = max(360, largura_pagina - 420 - 40 - 120)
        tamanho_titulo = max(40, min(84, int(largura_texto / 8.8)))
        apresentacao = ft.Column([
            titulo("OBJECTION!", tamanho_titulo, no_wrap=True),
            texto("The Art of Deception", 32, tema.LATAO, "FellItalico"),
            ft.Container(height=18),
            texto("Você defende o réu diante de um juiz que não se deixa enganar com facilidade.",
                  20, tema.CREME),
            texto("Cada argumento, blefe e prova muda o que o juiz pensa de você.",
                  20, tema.CREME_APAGADO),
        ], spacing=4, width=largura_texto)
        self._mostrar(ft.Container(
            content=ft.Row([apresentacao, ft.Column([formulario], tight=True)], spacing=40,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=60, vertical=40), expand=True))

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
        if self.usuario.nivel.value == "veterano":
            return "veterano"
        partidas, n_partidas, vitorias, n_vitorias = self.usuario.progresso_promocao()
        return (f"novato. Para virar veterano: {partidas} de {n_partidas} partidas concluídas "
                f"e {vitorias} de {n_vitorias} vitórias")

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
            acoes = []
            if ativa:
                acoes.append(botao("Continuar", lambda e, i=p.id: self.continuar_partida(i), "papel"))
            acoes.extend([
                botao("Renomear", lambda e, p=p: self.renomear_partida(p), "papel"),
                botao("Excluir", lambda e, p=p: self.excluir_partida(p), "papel"),
            ])
            salvas.append(folha(ft.Column([
                ft.Column([texto(p.nome, 17, tema.TINTA, "CorpoMedio"),
                           texto(situacao, 15, "#6B6459", "CorpoItalico")], spacing=0, tight=True),
                ft.Row(acoes, spacing=8, wrap=True),
            ], spacing=8, tight=True),
                faixa_cor=tema.LATAO, padding=12))
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
        self._mostrar(tela_admin(self))

    # ------------------------------------------------- gerenciar partidas
    def renomear_partida(self, partida):
        novo = campo("Novo nome", partida.nome, autofocus=True, max_length=60)
        dialogo_formulario(
            self, "Renomear partida", [novo],
            lambda: self.sessao.partidas.renomear(self.usuario, partida.id, novo.value),
            self.mostrar_home)

    def excluir_partida(self, partida):
        def excluir():
            self.sessao.partidas.excluir(self.usuario, partida.id)
            self.mostrar_home()

        dialogo_confirmacao(self, "Excluir partida",
                            f"“{partida.nome}” e as anotações dela serão apagadas. Isso não pode ser desfeito.",
                            excluir, "Excluir")

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
        self._reiniciar_ia()
        self.mostrar_partida()

    def continuar_partida(self, id_partida):
        try:
            self.ctrl = ControladorPartida.continuar(self.sessao, self.usuario, id_partida)
        except ObjectionException as erro:
            self._aviso(str(erro), erro=True)
            return
        self.fala, self.narracao = None, []
        self._reiniciar_ia()
        self.mostrar_partida()

    # ---------------------------------------------------------------- partida
    def _reiniciar_ia(self):
        self.usar_ia, self.carregando, self.fonte_fala, self.aviso_ia = False, False, "local", None

    def _alternar_ia(self, valor):
        self.usar_ia = bool(valor)
        self.page.update()

    def _bloco_ia(self):
        """Chave do modo online e saldos diário e por caso."""
        if not self.sessao.ia_disponivel(self.ctrl.juiz.id):
            return texto("Este juiz fala só com frases pré-escritas (nenhuma IA configurada).", 14,
                         tema.CREME_APAGADO, "CorpoItalico")
        energia = self.sessao.tokens.energia(self.usuario)
        sem_energia = energia == 0
        saldo_diario, limite_diario = self.sessao.tokens.saldo_diario(self.usuario)
        restante_caso, limite_caso = self.sessao.tokens.cota_caso(self.usuario, self.ctrl.partida.id_caso)
        nota = (f"Energia diária: {energia}% ({saldo_diario} de {limite_diario} tokens). "
                f"Cota deste caso: {restante_caso} de {limite_caso} tokens.")
        if sem_energia:
            nota += " Sem energia: resgate uma oferta ou volte amanhã."
        elif restante_caso == 0:
            nota += " Limite deste caso atingido; use as opções prontas até amanhã."
        chave = ft.Switch(
            label="Juiz com IA (online)", value=self.usar_ia and not sem_energia, disabled=sem_energia,
            on_change=lambda e: self._alternar_ia(e.control.value), active_color=tema.LATAO,
            label_text_style=ft.TextStyle(color=tema.CREME, font_family="Corpo", size=16))
        return ft.Column([chave, texto(nota, 14, tema.CREME_APAGADO, "CorpoItalico")], spacing=2, tight=True)

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
            ft.Container(height=4), self._bloco_ia(),
        ], spacing=12, col={"xs": 12, "md": 3})

        if self.carregando:
            palco = texto("O juiz está ponderando...", 24, tema.CREME_APAGADO, "FellItalico")
        elif self.fala:
            origem = [texto(f"Fala gerada por IA ({self.fonte_fala}).", 14, tema.CREME_APAGADO, "CorpoItalico")] \
                if self.fonte_fala != "local" else []
            palco = ft.Container(
                content=ft.Column([
                    texto(f"{c.juiz.nome} diz:", 16, tema.LATAO, "CorpoMedio"),
                    texto(f"“{self.fala}”", 28, tema.CREME, "FellItalico"),
                    *origem,
                ], spacing=6),
                border=ft.Border.only(left=ft.BorderSide(3, tema.LATAO)),
                padding=ft.Padding.only(left=18, top=4, bottom=4))
        else:
            dica = ("Reúna provas antes de entrar em julgamento. Cada ação custa créditos."
                    if fase is FasePartida.PREPARACAO else "O julgamento chegou ao fim.")
            palco = texto(dica, 20, tema.CREME_APAGADO, "CorpoItalico")
        narracao = [texto(m, 16, tema.CREME_APAGADO) for m in self.narracao]
        if self.aviso_ia:
            narracao.append(texto(self.aviso_ia, 15, tema.CREME_APAGADO, "CorpoItalico"))

        opcoes = [folha_de_opcao(o, self.usar_opcao) for o in c.opcoes()]
        if fase is FasePartida.DELIBERACAO:
            opcoes = [texto("Não restam rodadas ou o juiz já viu o bastante. Peça o veredito.", 18,
                            tema.CREME)]
        fala_livre = []
        if fase is FasePartida.JULGAMENTO and self.usuario.pode(Permissao.ARGUMENTO_LIVRE):
            if self.usar_ia:
                caixa = campo("Seu argumento, com as suas palavras", max_length=280, multiline=True,
                              min_lines=2, max_lines=4)
                fala_livre = [folha(ft.Column([
                    texto("Argumento livre", 20, tema.TINTA, "Fell"),
                    texto("Use as provas que você descobriu. O juiz interpreta o que você disse e o jogo "
                          "calcula o efeito: quem argumenta bem tem muito menos risco.", 14, tema.TINTA,
                          "CorpoItalico"),
                    caixa,
                    botao("Argumentar", lambda e: self.argumento_livre(caixa.value), "papel"),
                ], spacing=8), faixa_cor=tema.VERDE_AUTOS, padding=12)]
            else:
                fala_livre = [texto("Ligue o Juiz com IA (online) para argumentar com as suas próprias palavras.",
                                    16, tema.CREME_APAGADO, "CorpoItalico")]
        coluna_centro = ft.Column([
            palco, *narracao, ft.Container(height=6),
            titulo("Suas opções" if opcoes else "", 26), *opcoes, *fala_livre,
        ], spacing=10, col={"xs": 12, "md": 6})

        dossie = [folha_de_evidencia(e) for e in c.dossie()] or [
            texto("Nenhuma prova descoberta ainda.", 16, tema.CREME_APAGADO, "CorpoItalico")]
        historico = [linha_de_historico(e) for e in c.historico()] or [
            texto("Ainda sem ações.", 16, tema.CREME_APAGADO, "CorpoItalico")]
        coluna_autos = ft.Column([
            titulo("Dossiê", 26), *dossie, ft.Container(height=6),
            titulo("Histórico", 26), *historico, ft.Container(height=6),
            titulo("Caderno", 26), *self._caderno_controles(),
        ], spacing=10, col={"xs": 12, "md": 3})

        self.carimbo = carimbo_objecao()
        conteudo = ft.Container(content=ft.Column([
            topo, ft.Container(height=8),
            ft.ResponsiveRow([coluna_juiz, coluna_centro, coluna_autos], spacing=28, run_spacing=24),
        ], scroll=ft.ScrollMode.AUTO, spacing=10), padding=32, expand=True)
        self._mostrar(ft.Stack([conteudo, self.carimbo], expand=True))

    # ---------------------------------------------------------------- caderno
    def _caderno_controles(self) -> list:
        notas = self.sessao.caderno.listar(self.usuario, self.ctrl.partida.id)
        saida = []
        for a in notas:
            citadas = ""
            if a.evidencias:
                citadas = " Provas: " + ", ".join(a.evidencias) + "."
            saida.append(folha(ft.Column([
                texto(a.titulo, 17, tema.TINTA, "CorpoMedio"),
                *([texto(a.texto, 15, tema.TINTA)] if a.texto else []),
                *([texto(citadas.strip(), 14, tema.TINTA, "CorpoItalico")] if citadas else []),
                ft.Row([botao("Editar", lambda e, a=a: self.dialogo_anotacao(a), "papel"),
                        botao("Excluir", lambda e, a=a: self.excluir_anotacao(a), "papel")],
                       spacing=8, wrap=True),
            ], spacing=4), faixa_cor=tema.PAPEL_ESCURO, padding=10))
        if not notas:
            saida.append(texto("Anote suas teorias aqui.", 16, tema.CREME_APAGADO, "CorpoItalico"))
        saida.append(botao("Nova anotação", lambda e: self.dialogo_anotacao(), "secundario"))
        return saida

    def dialogo_anotacao(self, anotacao=None):
        titulo_campo = campo("Título", anotacao.titulo if anotacao else "", autofocus=True, max_length=60)
        texto_campo = campo("Anotação", anotacao.texto if anotacao else "", multiline=True,
                            min_lines=3, max_lines=6, max_length=600)
        provas = [(e, caixa(e.descricao[:70] + ("..." if len(e.descricao) > 70 else ""),
                            bool(anotacao and e.id in anotacao.evidencias)))
                  for e in self.ctrl.dossie()]
        rotulo_provas = ([texto("Provas citadas (só as já descobertas)", 15, tema.TINTA, "CorpoMedio")]
                         if provas else [])

        def salvar():
            citadas = [e.id for e, cx in provas if cx.value]
            if anotacao is None:
                self.sessao.caderno.criar(self.usuario, self.ctrl.partida.id, titulo_campo.value,
                                          texto_campo.value, citadas)
            else:
                self.sessao.caderno.editar(self.usuario, anotacao.id, titulo_campo.value,
                                           texto_campo.value, citadas)

        dialogo_formulario(self, "Editar anotação" if anotacao else "Nova anotação",
                           [titulo_campo, texto_campo, *rotulo_provas, *[cx for _, cx in provas]],
                           salvar, self.mostrar_partida)

    def excluir_anotacao(self, anotacao):
        def excluir():
            self.sessao.caderno.excluir(self.usuario, anotacao.id)
            self.mostrar_partida()

        dialogo_confirmacao(self, "Excluir anotação", f"Apagar “{anotacao.titulo}”?", excluir, "Excluir")

    @staticmethod
    def _faixa_confianca_texto(valor):
        from objection.dominio.regras import faixa_confianca
        return faixa_confianca(valor).value

    def usar_opcao(self, id_acao):
        if self.ocupado:
            return
        self.ocupado = True
        try:
            if self.usar_ia:
                self.carregando = True
                self.mostrar_partida()  # mostra "ponderando" enquanto a IA responde
            try:
                turno = self.ctrl.executar(id_acao, usar_ia=self.usar_ia)
            except ObjectionException as erro:
                self.carregando = False
                self._aviso(str(erro), erro=True)
                self.mostrar_partida()
                return
            self._aplicar_turno(turno)
        finally:
            self.ocupado = False

    def argumento_livre(self, texto_argumento):
        if self.ocupado:
            return
        self.ocupado = True
        try:
            self.carregando = True
            self.mostrar_partida()  # "ponderando": a IA faz até duas chamadas (interpretar e responder)
            try:
                turno = self.ctrl.argumento_livre(texto_argumento, usar_ia=self.usar_ia)
            except ObjectionException as erro:
                self.carregando = False
                self._aviso(str(erro), erro=True)
                self.mostrar_partida()
                return
            self._aplicar_turno(turno)
        finally:
            self.ocupado = False

    def _aplicar_turno(self, turno):
        self.carregando = False
        self.narracao = list(turno.motivos)
        self.fonte_fala, self.aviso_ia = turno.fonte, turno.aviso
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
