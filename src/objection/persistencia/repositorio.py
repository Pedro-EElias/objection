import json
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Generic, Optional, TypeVar

from objection.excecoes import DadosCorrompidosException, VersaoConflitanteException

T = TypeVar("T")


class Repositorio(ABC, Generic[T]):
    """Contrato genérico de armazenamento de objetos de domínio."""

    @abstractmethod
    def salvar(self, entidade: T) -> None: ...

    @abstractmethod
    def buscar_por_id(self, id_entidade: str) -> Optional[T]: ...

    @abstractmethod
    def listar(self) -> list: ...

    @abstractmethod
    def remover(self, id_entidade: str) -> bool: ...


class RepositorioJson(Repositorio[T]):
    """Guarda cada entidade num arquivo JSON, com cópia de segurança e lock otimista.

    - Carrega o arquivo ao iniciar.
    - Cada registro tem uma versão. Ao salvar, a versão que ESTA instância leu precisa ser
      igual à versão atual do arquivo; senão outra janela mexeu antes (VersaoConflitanteException).
    - A gravação é atômica (arquivo temporário + os.replace) e mantém um .bak do estado anterior.
    """

    def __init__(self, caminho, para_dict: Callable[[T], dict],
                 de_dict: Callable[[dict], T], obter_id: Callable[[T], str]):
        self._caminho = Path(caminho)
        self._backup = self._caminho.with_suffix(self._caminho.suffix + ".bak")
        self._para_dict = para_dict
        self._de_dict = de_dict
        self._obter_id = obter_id
        self._cache = {}
        self._versoes_lidas = {}
        self.recarregar()

    # --- leitura ---
    def recarregar(self):
        registros = self._ler_disco()
        self._cache = {i: self._de_dict(r["dados"]) for i, r in registros.items()}
        self._versoes_lidas = {i: r["versao"] for i, r in registros.items()}

    def buscar_por_id(self, id_entidade):
        return self._cache.get(id_entidade)

    def listar(self):
        return list(self._cache.values())

    # --- escrita ---
    def salvar(self, entidade):
        id_ = self._obter_id(entidade)
        disco = self._ler_disco()
        self._checar_versao(id_, disco)
        nova = disco.get(id_, {}).get("versao", 0) + 1
        disco[id_] = {"versao": nova, "dados": self._para_dict(entidade)}
        self._gravar(disco)
        self._versoes_lidas[id_] = nova
        self._cache[id_] = entidade

    def remover(self, id_entidade):
        disco = self._ler_disco()
        if id_entidade not in disco and id_entidade not in self._cache:
            return False
        self._checar_versao(id_entidade, disco)
        disco.pop(id_entidade, None)
        self._gravar(disco)
        self._cache.pop(id_entidade, None)
        self._versoes_lidas.pop(id_entidade, None)
        return True

    # --- internos ---
    def _checar_versao(self, id_, disco):
        atual = disco.get(id_, {}).get("versao")
        if atual != self._versoes_lidas.get(id_):
            raise VersaoConflitanteException(
                f"O registro '{id_}' foi alterado por outra instância; recarregue e tente de novo."
            )

    @staticmethod
    def _parse(caminho: Path) -> dict:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
        registros = conteudo["registros"]
        if not isinstance(registros, dict):
            raise ValueError("estrutura inválida")
        for r in registros.values():
            if not isinstance(r["versao"], int) or not isinstance(r["dados"], dict):
                raise ValueError("registro inválido")
        return registros

    def _ler_disco(self) -> dict:
        if not self._caminho.exists():
            return {}
        try:
            return self._parse(self._caminho)
        except (ValueError, KeyError, TypeError):  # JSONDecodeError é ValueError
            if self._backup.exists():
                try:
                    registros = self._parse(self._backup)
                except (ValueError, KeyError, TypeError):
                    registros = None
                if registros is not None:
                    shutil.copy2(self._backup, self._caminho)  # restaura o último estado bom
                    return registros
            raise DadosCorrompidosException(
                f"O arquivo '{self._caminho.name}' está corrompido e não há cópia de segurança válida."
            ) from None

    def _gravar(self, registros: dict):
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        if self._caminho.exists():
            shutil.copy2(self._caminho, self._backup)
        temporario = self._caminho.with_suffix(self._caminho.suffix + ".tmp")
        temporario.write_text(
            json.dumps({"registros": registros}, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporario, self._caminho)
