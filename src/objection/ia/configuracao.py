"""Leitura e validação das variáveis de ambiente de IA. Chaves nunca aparecem em logs ou mensagens."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from objection.excecoes import ConfiguracaoIAException

PROVEDORES_CONHECIDOS = frozenset({"gemini", "groq", "deepseek", "local"})
JUIZES_CONHECIDOS = frozenset({"formalista", "pragmatico", "cinico"})
CADEIAS_PADRAO = {"formalista": ("gemini", "local"), "pragmatico": ("local",), "cinico": ("local",)}


def carregar_env(caminho, env=None) -> int:
    """Lê um arquivo .env simples (CHAVE=valor) sem sobrescrever o que já está no ambiente."""
    env = os.environ if env is None else env
    caminho = Path(caminho)
    if not caminho.exists():
        return 0
    carregadas = 0
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave, valor = chave.strip(), valor.strip().strip('"').strip("'")
        if chave and valor and not env.get(chave):
            env[chave] = valor
            carregadas += 1
    return carregadas


def _numero(env, nome, padrao, tipo, minimo, maximo):
    bruto = (env.get(nome) or "").strip()
    if not bruto:
        return padrao
    try:
        valor = tipo(bruto)
    except ValueError:
        raise ConfiguracaoIAException(f"A variável {nome} deve ser um número.") from None
    if not minimo <= valor <= maximo:
        raise ConfiguracaoIAException(f"A variável {nome} deve estar entre {minimo} e {maximo}.")
    return valor


def _cadeias(env) -> dict:
    cadeias = {k: tuple(v) for k, v in CADEIAS_PADRAO.items()}
    bruto = (env.get("IA_CADEIAS") or "").strip()
    if not bruto:
        return cadeias
    for trecho in bruto.split(";"):
        juiz, _, lista = trecho.partition(":")
        juiz = juiz.strip()
        nomes = [n.strip() for n in lista.split(",") if n.strip()]
        if juiz not in JUIZES_CONHECIDOS or not nomes or not set(nomes) <= PROVEDORES_CONHECIDOS:
            raise ConfiguracaoIAException(
                "A variável IA_CADEIAS é inválida. Exemplo: formalista:gemini,local;pragmatico:local")
        if "local" not in nomes:
            nomes.append("local")  # o jogo nunca fica sem resposta
        cadeias[juiz] = tuple(nomes)
    return cadeias


@dataclass(frozen=True)
class ConfiguracaoIA:
    chave_gemini: str = field(default="", repr=False)
    modelo_gemini: str = ""
    timeout_segundos: float = 8.0
    max_tokens_saida: int = 512
    cadeias: dict = field(default_factory=lambda: {k: tuple(v) for k, v in CADEIAS_PADRAO.items()})

    @property
    def gemini_configurado(self) -> bool:
        return bool(self.chave_gemini and self.modelo_gemini)

    def __repr__(self):
        chave = "definida" if self.chave_gemini else "ausente"
        return (f"ConfiguracaoIA(chave_gemini={chave}, modelo_gemini={self.modelo_gemini!r}, "
                f"timeout_segundos={self.timeout_segundos}, max_tokens_saida={self.max_tokens_saida})")

    @classmethod
    def do_ambiente(cls, env=None) -> "ConfiguracaoIA":
        env = os.environ if env is None else env
        return cls(
            chave_gemini=(env.get("GEMINI_API_KEY") or "").strip(),
            modelo_gemini=(env.get("GEMINI_MODEL") or "").strip(),
            timeout_segundos=_numero(env, "IA_TIMEOUT_SEGUNDOS", 8.0, float, 1, 60),
            max_tokens_saida=_numero(env, "IA_MAX_TOKENS_SAIDA", 512, int, 64, 2048),
            cadeias=_cadeias(env),
        )
