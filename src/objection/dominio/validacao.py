"""Validações de tipo de dado (não contam como regras de negócio)."""
from objection.excecoes import DadosInvalidosException


def exigir_texto(valor, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidosException(f"O campo '{campo}' não pode ficar vazio.")
    return valor.strip()


def exigir_intervalo(valor, campo: str, minimo: int, maximo: int) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise DadosInvalidosException(
            f"{campo} deve ser um inteiro entre {minimo} e {maximo}."
        )
    return valor
