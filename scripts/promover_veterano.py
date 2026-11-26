"""Ferramenta de demonstração: promove um jogador a Veterano sem precisar jogar 3 partidas.

Uso:  python scripts/promover_veterano.py apelido [pasta_de_dados]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from objection.dominio.usuario import Jogador  # noqa: E402
from objection.persistencia.fabrica import criar_repositorios  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    apelido = sys.argv[1].lower()
    repos = criar_repositorios(Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data"))
    jogador = next((u for u in repos.usuarios.listar()
                    if isinstance(u, Jogador) and u.apelido.lower() == apelido), None)
    if jogador is None:
        print(f"Jogador '{sys.argv[1]}' não encontrado.")
        return 1
    for i in range(3):
        jogador.registrar_partida_concluida(f"demo-{i}", True)
    repos.usuarios.salvar(jogador)
    print(f"{jogador.apelido} agora é {jogador.nivel.value}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
