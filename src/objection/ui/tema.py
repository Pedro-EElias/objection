"""Identidade visual: bancada escura de tribunal, papel de autos e latão."""
import flet as ft

# Cores
CARVAO = "#1D1C1E"        # fundo (a bancada)
CARVAO_2 = "#2A2829"      # painéis sobre a bancada
VINHO = "#4B1A25"         # faixas e retrato
VINHO_VIVO = "#A33A3F"    # alerta, suspeita
PAPEL = "#D9CFB8"         # folhas de autos (opções e dossiê)
PAPEL_ESCURO = "#C4B99F"
TINTA = "#2A2423"         # texto sobre papel
CREME = "#EDE6D3"         # texto sobre a bancada
CREME_APAGADO = "#A89F8C" # texto secundário sobre a bancada
LATAO = "#B08D4F"         # molduras e destaques
VERDE_AUTOS = "#6F8468"   # categoria "argumento"

# Famílias de fonte (arquivos em assets/fonts)
FONTES = {
    "Fell": "fonts/IMFeENrm28P.ttf",
    "FellItalico": "fonts/IMFeENit28P.ttf",
    "Corpo": "fonts/AlegreyaSans-Regular.ttf",
    "CorpoMedio": "fonts/AlegreyaSans-Medium.ttf",
    "CorpoNegrito": "fonts/AlegreyaSans-Bold.ttf",
    "CorpoItalico": "fonts/AlegreyaSans-Italic.ttf",
}


def texto(valor, tam=16, cor=CREME, fam="Corpo", **extra) -> ft.Text:
    return ft.Text(valor, size=tam, color=cor, font_family=fam, **extra)


def titulo(valor, tam=34, cor=CREME, **extra) -> ft.Text:
    return texto(valor, tam, cor, "Fell", **extra)


def configurar_pagina(page: ft.Page):
    page.title = "OBJECTION! The Art of Deception"
    page.bgcolor = CARVAO
    page.padding = 0
    page.fonts = FONTES
    page.theme = ft.Theme(font_family="Corpo")
    page.window.width = 1240
    page.window.height = 800
    page.window.min_width = 980
    page.window.min_height = 680


def botao(rotulo, ao_clicar, tipo="principal", desabilitado=False, largura=None, icone=None) -> ft.Button:
    """principal: latão cheio. secundario: contorno. perigo: vinho vivo."""
    estilos = {
        "principal": (LATAO, CARVAO, None),
        "secundario": (None, CREME, ft.BorderSide(1, CREME_APAGADO)),
        "perigo": (VINHO_VIVO, CREME, None),
        "papel": (CARVAO, CREME, None),
    }
    fundo, cor, borda = estilos[tipo]
    return ft.Button(
        content=texto(rotulo, 16, cor, "CorpoNegrito"),
        icon=icone,
        on_click=ao_clicar,
        disabled=desabilitado,
        width=largura,
        style=ft.ButtonStyle(
            bgcolor=fundo,
            color=cor,
            side=borda,
            shape=ft.RoundedRectangleBorder(radius=2),
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
        ),
    )
