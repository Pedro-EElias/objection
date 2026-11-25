"""Cria (ou confirma) a conta de administrador e os pacotes padrão.

Uso:  python scripts/criar_admin.py [pasta_de_dados]     (padrão: data/)
A senha é pedida no terminal e nunca fica gravada no código.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from objection.excecoes import ObjectionException
from objection.persistencia.fabrica import criar_repositorios
from objection.servicos.autenticacao import ServicoAutenticacao
from objection.servicos.ofertas import garantir_pacotes_padrao


def main():
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    repos = criar_repositorios(pasta)
    garantir_pacotes_padrao(repos)
    apelido = input("Apelido do administrador: ").strip()
    senha = getpass.getpass("Senha (8+ caracteres, com maiúscula, minúscula, número e especial): ")
    try:
        ServicoAutenticacao(repos).cadastrar_administrador(apelido, senha)
    except ObjectionException as erro:
        print(f"Não foi possível criar: {erro}")
        return 1
    print(f"Administrador '{apelido}' criado em {pasta}/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
