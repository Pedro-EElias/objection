from dataclasses import dataclass
from typing import Callable

from objection.casos import caso_1
from objection.excecoes import DadosInvalidosException


@dataclass(frozen=True)
class EntradaCaso:
    id: str
    titulo: str
    sinopse: str
    criar_caso: Callable
    criar_opcoes: Callable


_CATALOGO = {
    caso_1.ID: EntradaCaso(caso_1.ID, "A Relíquia Desaparecida", caso_1.SINOPSE,
                           caso_1.criar_caso, caso_1.criar_opcoes),
}


def listar_casos() -> list:
    return list(_CATALOGO.values())


def obter_caso(id_caso: str) -> EntradaCaso:
    try:
        return _CATALOGO[id_caso]
    except KeyError:
        raise DadosInvalidosException(f"Caso desconhecido: {id_caso}") from None
