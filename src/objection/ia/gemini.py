import json
import socket
import urllib.error
import urllib.request
from typing import Callable

from objection.excecoes import (
    ConfiguracaoIAException,
    ProvedorIAIndisponivelException,
    RespostaIAInvalidaException,
)
from objection.ia.contexto import Interpretacao
from objection.ia.contrato import (
    ESQUEMA_GEMINI, esquema_interpretacao, validar_interpretacao, validar_resposta,
)
from objection.ia.prompt import construir_prompt, construir_prompt_interpretacao
from objection.ia.provedor_base import ProvedorIA, ReacaoJuiz

LIMITE_RESPOSTA = 256 * 1024
URL_MODELO = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


def enviar_urllib(url: str, cabecalhos: dict, corpo: bytes, timeout: float):
    """Envia a requisição. As mensagens de erro nunca incluem URL nem cabeçalhos."""
    requisicao = urllib.request.Request(url, data=corpo, headers=cabecalhos, method="POST")
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return resposta.status, resposta.read(LIMITE_RESPOSTA)
    except urllib.error.HTTPError as erro:
        return erro.code, b""
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError):
        raise ProvedorIAIndisponivelException("Sem resposta do provedor (rede ou tempo esgotado).") from None


class ProvedorGemini(ProvedorIA):
    """Adaptador da API REST do Gemini. O modelo vem de GEMINI_MODEL (não fica fixo no código)."""

    nome = "gemini"

    def __init__(self, config, enviar: Callable = enviar_urllib):
        if not config.gemini_configurado:
            raise ConfiguracaoIAException("Defina GEMINI_API_KEY e GEMINI_MODEL para usar o Gemini.")
        self._config = config
        self._enviar = enviar

    def estimar_tokens(self, juiz, contexto) -> int:
        sistema, usuario = construir_prompt(juiz, contexto)
        return max(1, (len(sistema) + len(usuario)) // 4) + self._config.max_tokens_saida

    def estimar_tokens_interpretacao(self, contexto) -> int:
        sistema, usuario = construir_prompt_interpretacao(contexto)
        return max(1, (len(sistema) + len(usuario)) // 4) + self._config.max_tokens_saida

    def _corpo(self, sistema: str, usuario: str, esquema: dict) -> dict:
        return {
            "systemInstruction": {"parts": [{"text": sistema}]},
            "contents": [{"role": "user", "parts": [{"text": usuario}]}],
            "generationConfig": {
                "temperature": 0.8 if esquema is ESQUEMA_GEMINI else 0.0,
                "maxOutputTokens": self._config.max_tokens_saida,
                "responseMimeType": "application/json",
                "responseSchema": esquema,
            },
        }

    def _requisitar(self, sistema: str, usuario: str, esquema: dict) -> tuple:
        """Faz a chamada e devolve (texto, tokens de entrada, tokens de saída)."""
        url = URL_MODELO.format(modelo=self._config.modelo_gemini)
        # A chave vai no cabeçalho, nunca na URL (URLs aparecem em logs).
        cabecalhos = {"Content-Type": "application/json", "x-goog-api-key": self._config.chave_gemini}
        corpo = json.dumps(self._corpo(sistema, usuario, esquema)).encode("utf-8")
        status, bruto = self._enviar(url, cabecalhos, corpo, self._config.timeout_segundos)
        if status != 200:
            raise ProvedorIAIndisponivelException(f"O provedor respondeu com o código {status}.")
        try:
            dados = json.loads(bruto.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise RespostaIAInvalidaException("O provedor devolveu algo que não é JSON.") from None
        return self._extrair(dados, sistema + usuario)

    def gerar_reacao(self, juiz, contexto) -> ReacaoJuiz:
        sistema, usuario = construir_prompt(juiz, contexto)
        texto, entrada, saida = self._requisitar(sistema, usuario, ESQUEMA_GEMINI)
        validada = validar_resposta(texto, contexto.classificacao)
        return ReacaoJuiz(validada.dialogo, False, provedor=self.nome,
                          tokens_entrada=entrada, tokens_saida=saida, simulado=False)

    def interpretar(self, contexto) -> Interpretacao:
        """Diz quais afirmações do caso o argumento livre faz. Só etiquetas da lista fechada passam."""
        sistema, usuario = construir_prompt_interpretacao(contexto)
        etiquetas = set(contexto.afirmacoes_possiveis)
        texto, entrada, saida = self._requisitar(sistema, usuario, esquema_interpretacao(etiquetas))
        validada = validar_interpretacao(texto, etiquetas)
        return Interpretacao(validada.afirmacoes, validada.clareza, self.nome, entrada, saida,
                             validada.conduta_inadequada)

    @staticmethod
    def _extrair(dados, prompt: str) -> tuple:
        if not isinstance(dados, dict):
            raise RespostaIAInvalidaException("Resposta do provedor em formato inesperado.")
        if (dados.get("promptFeedback") or {}).get("blockReason"):
            raise ProvedorIAIndisponivelException("O provedor bloqueou esta solicitação.")
        candidatos = dados.get("candidates") or []
        if not candidatos or not isinstance(candidatos[0], dict):
            raise ProvedorIAIndisponivelException("O provedor não devolveu nenhuma resposta.")
        candidato = candidatos[0]
        if candidato.get("finishReason") in ("SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT"):
            raise ProvedorIAIndisponivelException("O provedor bloqueou esta resposta.")
        partes = (candidato.get("content") or {}).get("parts") or []
        texto = "".join(p.get("text", "") for p in partes if isinstance(p, dict))
        uso = dados.get("usageMetadata") or {}
        entrada = uso.get("promptTokenCount")
        saida = uso.get("candidatesTokenCount")
        entrada = entrada if isinstance(entrada, int) and entrada >= 0 else max(1, len(prompt) // 4)
        saida = saida if isinstance(saida, int) and saida >= 0 else max(1, len(texto) // 4)
        return texto, entrada, saida
