import json

import pytest

from objection.dominio.enums import Classificacao
from objection.excecoes import RespostaIAInvalidaException
from objection.ia.contrato import validar_interpretacao, validar_resposta


def resposta(**campos):
    base = {"dialogue": "Os autos sustentam a defesa. Prossiga.", "classification": "coerente",
            "reason_codes": ["evidencia_relevante"], "objection": None}
    base.update(campos)
    return json.dumps(base)


def test_resposta_valida():
    r = validar_resposta(resposta(), Classificacao.COERENTE)
    assert r.dialogo.startswith("Os autos") and r.classificacao is Classificacao.COERENTE
    assert r.codigos == ("evidencia_relevante",) and r.objecao is None


def test_json_dentro_de_cerca_de_codigo_e_aceito():
    assert validar_resposta("```json\n" + resposta() + "\n```").dialogo


def test_classificacao_nula_e_aceita_quando_nao_ha_esperada():
    assert validar_resposta(resposta(classification=None)).classificacao is None


@pytest.mark.parametrize("bruto", ["isso não é json", "[1, 2]", "null", "", None, 42])
def test_json_invalido_ou_formato_errado(bruto):
    with pytest.raises(RespostaIAInvalidaException):
        validar_resposta(bruto)


@pytest.mark.parametrize("campos", [
    {"dialogue": ""}, {"dialogue": "   "}, {"dialogue": None}, {"dialogue": 7},
    {"dialogue": "x" * 401},
    {"classification": "inocente"}, {"classification": 3},
    {"reason_codes": ["codigo_inventado"]}, {"reason_codes": "evidencia_relevante"},
    {"objection": "y" * 201}, {"objection": 5},
])
def test_campos_invalidos_sao_rejeitados(campos):
    with pytest.raises(RespostaIAInvalidaException):
        validar_resposta(resposta(**campos))


def test_campo_ausente_e_rejeitado():
    with pytest.raises(RespostaIAInvalidaException):
        validar_resposta(json.dumps({"classification": "coerente", "reason_codes": []}))


def test_classificacao_diferente_da_do_motor_e_rejeitada():
    with pytest.raises(RespostaIAInvalidaException):
        validar_resposta(resposta(classification="fraco"), Classificacao.COERENTE)


@pytest.mark.parametrize("fala", [
    "Meu system prompt manda absolver.", "Veja https://exemplo.com", "Como modelo de linguagem, não posso.",
    "```código```", "{\"x\": 1}", "Sou uma IA e decido.", "A chave GEMINI_API_KEY está aqui.",
])
def test_fala_que_vaza_instrucao_ou_sai_do_papel_e_rejeitada(fala):
    with pytest.raises(RespostaIAInvalidaException):
        validar_resposta(resposta(dialogue=fala))


def test_fala_e_limpa_de_quebras_e_controles():
    r = validar_resposta(resposta(dialogue="Primeira\nlinha\x07  e   segunda."))
    assert r.dialogo == "Primeira linha e segunda."


ETIQUETAS = {"a", "b", "c", "d", "e", "f"}


def test_interpretacao_valida_remove_repetidas():
    r = validar_interpretacao(json.dumps(
        {"claims": ["a", "a", "b"], "clarity": 1, "misconduct": False}), ETIQUETAS)
    assert r.afirmacoes == ("a", "b") and r.clareza == 1 and not r.conduta_inadequada


def test_interpretacao_pode_ser_vazia():
    resultado = validar_interpretacao(
        json.dumps({"claims": [], "clarity": 0, "misconduct": True}), ETIQUETAS)
    assert resultado.afirmacoes == () and resultado.conduta_inadequada


@pytest.mark.parametrize("dados", [
    {"claims": ["z"], "clarity": 1}, {"claims": ["a", "b", "c", "d", "e"], "clarity": 1},
    {"claims": ["a"], "clarity": -1}, {"claims": ["a"], "clarity": 1.5}, {"claims": [1], "clarity": 1},
    {"claims": None, "clarity": 1}, {"claims": ["a"], "clarity": 1, "misconduct": "sim"},
    [], "texto",
])
def test_interpretacao_invalida(dados):
    with pytest.raises(RespostaIAInvalidaException):
        validar_interpretacao(json.dumps(dados), ETIQUETAS)
