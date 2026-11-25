"""Dados e leitura de formulários do painel do administrador (sem código de tela)."""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from objection.dominio.usuario import Jogador
from objection.excecoes import DadosInvalidosException


@dataclass(frozen=True)
class LinhaConta:
    id: str
    apelido: str
    nivel: str
    status: str
    energia: int
    saldo: int
    cota_diaria: int
    cota_por_caso: int
    partidas: int
    vitorias: int


def linhas_de_contas(sessao, admin) -> list:
    """Uma linha por jogador, com a carteira de tokens (o administrador vê os números reais)."""
    linhas = []
    for u in sessao.administracao.listar_contas(admin):
        if not isinstance(u, Jogador):
            continue
        c = sessao.tokens.carteira_atual(u.id)
        linhas.append(LinhaConta(
            u.id, u.apelido, u.nivel.value, u.status.value, c.energia_percentual, c.saldo,
            c.cota_diaria, c.cota_por_caso, len(u.partidas_concluidas), u.vitorias))
    return sorted(linhas, key=lambda linha: linha.apelido.lower())


def ler_inteiro(valor, campo: str, opcional=False, minimo=0) -> Optional[int]:
    texto = (valor or "").strip()
    if not texto:
        if opcional:
            return None
        raise DadosInvalidosException(f"Preencha {campo}.")
    try:
        numero = int(texto)
    except ValueError:
        raise DadosInvalidosException(f"{campo} deve ser um número inteiro.") from None
    if numero < minimo:
        raise DadosInvalidosException(f"{campo} não pode ser menor que {minimo}.")
    return numero


def ler_data(valor, campo: str) -> Optional[date]:
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise DadosInvalidosException(f"{campo} deve estar no formato AAAA-MM-DD.") from None
