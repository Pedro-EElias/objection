from dataclasses import dataclass
from pathlib import Path

from objection.persistencia import serializadores as sz
from objection.persistencia.repositorio import RepositorioJson


@dataclass
class Repositorios:
    usuarios: RepositorioJson
    carteiras: RepositorioJson
    consumos: RepositorioJson
    pacotes: RepositorioJson
    resgates: RepositorioJson
    partidas: RepositorioJson


def criar_repositorios(pasta) -> Repositorios:
    """Cria os seis repositórios JSON dentro da pasta de dados (carrega o que já existir)."""
    pasta = Path(pasta)
    return Repositorios(
        usuarios=RepositorioJson(pasta / "usuarios.json", sz.usuario_para_dict, sz.usuario_de_dict, lambda u: u.id),
        carteiras=RepositorioJson(pasta / "carteiras.json", sz.carteira_para_dict, sz.carteira_de_dict, lambda c: c.id_conta),
        consumos=RepositorioJson(pasta / "consumos.json", sz.consumo_para_dict, sz.consumo_de_dict, lambda r: r.id),
        pacotes=RepositorioJson(pasta / "pacotes.json", sz.pacote_para_dict, sz.pacote_de_dict, lambda p: p.id),
        resgates=RepositorioJson(pasta / "resgates.json", sz.resgate_para_dict, sz.resgate_de_dict, lambda r: r.id),
        partidas=RepositorioJson(pasta / "partidas.json", sz.partida_para_dict, sz.partida_de_dict, lambda p: p.id),
    )
