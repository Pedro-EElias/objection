from pathlib import Path

import flet as ft

from objection.ui import tema
from objection.ui.tema import botao, texto, titulo

RAIZ_ASSETS = Path(__file__).resolve().parents[3] / "assets"

_ICONES = {
    "investigar": ft.Icons.SEARCH,
    "testemunha": ft.Icons.RECORD_VOICE_OVER,
    "alibi": ft.Icons.SCHEDULE,
    "suborno": ft.Icons.PAYMENTS,
    "argumento": ft.Icons.BALANCE,
    "blefe": ft.Icons.THEATER_COMEDY,
}
_NOMES = {
    "investigar": "Investigação", "testemunha": "Testemunha", "alibi": "Álibi",
    "suborno": "Suborno", "argumento": "Argumento", "blefe": "Blefe",
}
_FAIXA_CONFIANCA = {"hostil": "hostil", "desconfiado": "desconfiado",
                    "receptivo": "receptivo", "convencido": "convencido"}


def _iniciais(nome: str) -> str:
    partes = [p for p in nome.split() if p]
    return (partes[0][0] + partes[-1][0]).upper()


def retrato(juiz, largura=150) -> ft.Control:
    """Moldura de latão. Se existir assets/juizes/<id>.png usa a imagem; senão, o monograma."""
    altura = round(largura * 1.25)
    imagem = RAIZ_ASSETS / "juizes" / f"{juiz.id}.png"
    if imagem.exists():
        miolo = ft.Image(src=f"juizes/{juiz.id}.png", width=largura, height=altura, fit=ft.BoxFit.COVER)
    else:
        miolo = ft.Container(
            content=titulo(_iniciais(juiz.nome), tam=round(largura * 0.4), cor=tema.LATAO),
            alignment=ft.Alignment.CENTER, bgcolor=tema.VINHO, width=largura, height=altura)
    return ft.Container(
        content=miolo, border=ft.Border.all(2, tema.LATAO), padding=4,
        width=largura + 12, height=altura + 12)


def placa_do_juiz(juiz) -> ft.Control:
    return ft.Column(
        [titulo(juiz.nome, 24), texto(juiz.titulo, 15, tema.CREME_APAGADO)],
        spacing=0, tight=True)


def medidor(rotulo, valor, maximo, cor, complemento="") -> ft.Control:
    """Barra com número e palavra: o significado nunca depende só da cor."""
    return ft.Column([
        ft.Row([texto(rotulo, 16, tema.CREME, "CorpoMedio"),
                texto(f"{valor}" + (f"  {complemento}" if complemento else ""), 16, tema.CREME)],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.ProgressBar(value=0 if maximo == 0 else min(1, valor / maximo), color=cor,
                       bgcolor=tema.CARVAO_2, bar_height=8, border_radius=0),
    ], spacing=4, tight=True)


def faixa_suspeita(valor: int) -> str:
    return "baixa" if valor < 30 else "média" if valor < 60 else "alta"


def folha(conteudo, faixa_cor=None, largura=None, padding=14) -> ft.Container:
    """Folha de autos. A faixa lateral codifica o tipo (investigação, argumento, blefe...)."""
    borda = ft.Border.only(left=ft.BorderSide(4, faixa_cor)) if faixa_cor else None
    return ft.Container(content=conteudo, bgcolor=tema.PAPEL, border=borda,
                        border_radius=2, padding=padding, width=largura)


def cor_da_categoria(categoria: str) -> str:
    return {"argumento": tema.VERDE_AUTOS, "blefe": tema.LATAO, "suborno": tema.VINHO_VIVO}.get(
        categoria, tema.PAPEL_ESCURO)


def folha_de_opcao(opcao, ao_usar) -> ft.Control:
    ativa = opcao.estado == "disponivel"
    cor_texto = tema.TINTA if ativa else "#6B6459"
    custo = f"Custa {opcao.custo} créditos" if opcao.custo else "Sem custo"
    detalhes = f"{_NOMES[opcao.categoria]}. Risco: {opcao.risco}. {custo}."
    if opcao.motivo:
        detalhes = f"{opcao.motivo}"
    if opcao.estado == "usada":
        acao = ft.Row([ft.Icon(ft.Icons.CHECK, color=tema.VERDE_AUTOS, size=20),
                       texto("Feito", 15, tema.TINTA, "CorpoMedio")], spacing=4)
    elif opcao.estado == "bloqueada":
        acao = ft.Icon(ft.Icons.LOCK_OUTLINE, color="#6B6459", size=22)
    else:
        acao = botao("Usar", lambda e, i=opcao.id: ao_usar(i), "papel")
    return folha(
        ft.Row([
            ft.Icon(_ICONES[opcao.categoria], color=cor_texto, size=24),
            ft.Column([texto(opcao.texto, 18, cor_texto, "CorpoMedio"),
                       texto(detalhes, 14, cor_texto, "CorpoItalico")], spacing=2, expand=True),
            acao,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        faixa_cor=cor_da_categoria(opcao.categoria) if ativa else tema.PAPEL_ESCURO)


def folha_de_evidencia(ev) -> ft.Control:
    return folha(ft.Column([
        texto(ev.descricao, 16, tema.TINTA, "CorpoMedio"),
        texto(f"{ev.origem}. Confiabilidade {ev.confiabilidade} de 100.", 14, tema.TINTA, "CorpoItalico"),
    ], spacing=2, tight=True), faixa_cor=tema.LATAO, padding=10)


def linha_de_historico(evento) -> ft.Control:
    sinal = lambda n: f"+{n}" if n > 0 else str(n)
    resumo = f"Confiança {sinal(evento.delta_confianca)}, suspeita {sinal(evento.delta_suspeita)}"
    return ft.Column([
        texto(evento.descricao, 15, tema.CREME, "CorpoMedio"),
        texto(resumo if (evento.delta_confianca or evento.delta_suspeita) else "Sem efeito nos indicadores",
              14, tema.CREME_APAGADO, "CorpoItalico"),
    ], spacing=0, tight=True)


def carimbo_objecao() -> ft.Container:
    """Único momento animado da tela: o carimbo bate e some."""
    return ft.Container(
        content=ft.Container(
            content=titulo("Objeção!", 72, tema.CREME),
            padding=ft.Padding.symmetric(horizontal=40, vertical=10),
            border=ft.Border.all(6, tema.VINHO_VIVO), bgcolor="#99300F18",
            rotate=ft.Rotate(-0.08)),
        alignment=ft.Alignment.CENTER, expand=True, opacity=0, scale=2.4,
        animate_opacity=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        ignore_interactions=True)
