"""Ponto de entrada do jogo.

    python main.py         abre a janela do jogo
    python main.py --web   abre no navegador (alternativa se a janela não abrir)
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

import flet as ft  # noqa: E402

from objection.app.controlador import SessaoApp  # noqa: E402
from objection.excecoes import ObjectionException  # noqa: E402
from objection.ia.configuracao import carregar_env  # noqa: E402
from objection.ui.app import AppUI  # noqa: E402


def main(page: ft.Page):
    carregar_env(RAIZ / ".env")  # chaves de IA (opcionais); nunca vão para o Git
    try:
        sessao = SessaoApp(RAIZ / "data")
    except ObjectionException as erro:
        page.add(ft.Text(f"Não foi possível iniciar: {erro}", color="#A33A3F", size=18))
        return
    AppUI(page, sessao).iniciar()


if __name__ == "__main__":
    visao = ft.AppView.WEB_BROWSER if "--web" in sys.argv else ft.AppView.FLET_APP
    ft.run(main, view=visao, assets_dir=str(RAIZ / "assets"))
