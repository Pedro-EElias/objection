"""Contrato da resposta da IA. Toda resposta é conteúdo NÃO confiável: só passa o que for válido."""
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from objection.dominio.enums import Classificacao
from objection.excecoes import RespostaIAInvalidaException

CODIGOS_CONHECIDOS = frozenset({
    "evidencia_relevante", "argumento_fraco", "sem_prova_descoberta", "contradicao_com_provas",
    "blefe_ousado", "blefe_fragil", "suborno_descoberto", "conduta_inadequada", "contexto_plausivel",
})
MAX_DIALOGO = 400
MAX_OBJECAO = 200
_VALORES = {c.value: c for c in Classificacao}

# Marcas de que o texto vazou instrução, saiu do papel ou traz conteúdo que não é fala de juiz.
_VAZAMENTO = re.compile(
    r"(system prompt|prompt do sistema|instru[cç][oõ]es do sistema|como (um )?modelo de linguagem|"
    r"sou uma ia|intelig[eê]ncia artificial|https?://|```|\{|\}|api[_ -]?key|gemini|openai|deepseek|groq)",
    re.IGNORECASE)

ESQUEMA_GEMINI = {
    "type": "OBJECT",
    "properties": {
        "dialogue": {"type": "STRING"},
        "classification": {"type": "STRING", "enum": sorted(_VALORES), "nullable": True},
        "reason_codes": {"type": "ARRAY", "items": {"type": "STRING", "enum": sorted(CODIGOS_CONHECIDOS)}},
        "objection": {"type": "STRING", "nullable": True},
    },
    "required": ["dialogue", "classification", "reason_codes"],
}


@dataclass(frozen=True)
class RespostaValidada:
    dialogo: str
    classificacao: Optional[Classificacao]
    codigos: tuple
    objecao: Optional[str]


def _limpar(texto: str) -> str:
    sem_controle = "".join(c for c in texto if unicodedata.category(c)[0] != "C" or c in "\n\t ")
    return re.sub(r"\s+", " ", sem_controle).strip()


def _extrair_json(bruto: str) -> dict:
    texto = bruto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE).strip()
    try:
        dados = json.loads(texto)
    except (ValueError, TypeError):
        raise RespostaIAInvalidaException("A resposta da IA não é um JSON válido.") from None
    if not isinstance(dados, dict):
        raise RespostaIAInvalidaException("A resposta da IA não é um objeto JSON.")
    return dados


def validar_resposta(bruto, classificacao_esperada: Optional[Classificacao] = None) -> RespostaValidada:
    """Valida o JSON da IA. Qualquer desvio levanta RespostaIAInvalidaException."""
    if not isinstance(bruto, str):
        raise RespostaIAInvalidaException("A resposta da IA está vazia.")
    dados = _extrair_json(bruto)

    dialogo = dados.get("dialogue")
    if not isinstance(dialogo, str) or not _limpar(dialogo):
        raise RespostaIAInvalidaException("A fala do juiz está ausente.")
    dialogo = _limpar(dialogo)
    if len(dialogo) > MAX_DIALOGO:
        raise RespostaIAInvalidaException("A fala do juiz é longa demais.")
    if _VAZAMENTO.search(dialogo):
        raise RespostaIAInvalidaException("A fala do juiz traz conteúdo fora do papel.")

    bruta = dados.get("classification")
    if bruta is None:
        classificacao = None
    elif isinstance(bruta, str) and bruta in _VALORES:
        classificacao = _VALORES[bruta]
    else:
        raise RespostaIAInvalidaException("A classificação devolvida não é conhecida.")
    if classificacao_esperada is not None and classificacao is not classificacao_esperada:
        raise RespostaIAInvalidaException("A classificação da IA diverge da calculada pelo motor.")

    codigos = dados.get("reason_codes", [])
    if not isinstance(codigos, list) or not all(isinstance(c, str) and c in CODIGOS_CONHECIDOS for c in codigos):
        raise RespostaIAInvalidaException("Os códigos de motivo devolvidos não são conhecidos.")

    objecao = dados.get("objection")
    if objecao is not None:
        if not isinstance(objecao, str) or len(_limpar(objecao)) > MAX_OBJECAO or _VAZAMENTO.search(objecao):
            raise RespostaIAInvalidaException("A objeção devolvida é inválida.")
        objecao = _limpar(objecao) or None
    return RespostaValidada(dialogo, classificacao, tuple(codigos), objecao)


MAX_AFIRMACOES = 4


@dataclass(frozen=True)
class InterpretacaoValidada:
    afirmacoes: tuple
    clareza: int
    conduta_inadequada: bool = False


def esquema_interpretacao(etiquetas) -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "claims": {"type": "ARRAY", "items": {"type": "STRING", "enum": sorted(etiquetas)}},
            "clarity": {"type": "INTEGER"},
            "misconduct": {"type": "BOOLEAN"},
        },
        "required": ["claims", "clarity", "misconduct"],
    }


def validar_interpretacao(bruto, etiquetas_validas) -> InterpretacaoValidada:
    """Valida a interpretação. Etiqueta fora da lista fechada ou clareza fora de 0..2 invalida tudo."""
    if not isinstance(bruto, str):
        raise RespostaIAInvalidaException("A interpretação da IA está vazia.")
    dados = _extrair_json(bruto)
    afirmacoes = dados.get("claims")
    if not isinstance(afirmacoes, list) or not all(isinstance(a, str) for a in afirmacoes):
        raise RespostaIAInvalidaException("A lista de afirmações devolvida é inválida.")
    if not set(afirmacoes) <= set(etiquetas_validas):
        raise RespostaIAInvalidaException("A IA devolveu uma afirmação que não existe no caso.")
    unicas = tuple(dict.fromkeys(afirmacoes))
    if len(unicas) > MAX_AFIRMACOES:
        raise RespostaIAInvalidaException("A IA devolveu afirmações demais.")
    clareza = dados.get("clarity")
    if isinstance(clareza, bool) or not isinstance(clareza, int) or not 0 <= clareza <= 2:
        raise RespostaIAInvalidaException("A clareza devolvida está fora do intervalo.")
    conduta_inadequada = dados.get("misconduct")
    if not isinstance(conduta_inadequada, bool):
        raise RespostaIAInvalidaException("A classificação de conduta devolvida é inválida.")
    return InterpretacaoValidada(unicas, clareza, conduta_inadequada)
