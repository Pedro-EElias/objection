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
from objection.ui.app import AppUI  # noqa: E402


def main(page: ft.Page):
    AppUI(page, SessaoApp(RAIZ / "data")).iniciar()


if __name__ == "__main__":
    visao = ft.AppView.WEB_BROWSER if "--web" in sys.argv else ft.AppView.FLET_APP
    ft.run(main, view=visao, assets_dir=str(RAIZ / "assets"))
