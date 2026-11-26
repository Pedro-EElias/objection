"""Teste manual de UMA chamada real ao Gemini, para validar a chave, o modelo e o formato.

Uso (na raiz do projeto, com o .env preenchido):  python scripts/testar_gemini.py
Não grava nada; só imprime o resultado. A chave nunca é impressa.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from objection.dominio.enums import Classificacao  # noqa: E402
from objection.dominio.juiz import JuizFormalista  # noqa: E402
from objection.excecoes import ObjectionException  # noqa: E402
from objection.ia.configuracao import ConfiguracaoIA, carregar_env  # noqa: E402
from objection.ia.contexto import ContextoInterpretacao, ContextoReacao  # noqa: E402
from objection.ia.gemini import ProvedorGemini  # noqa: E402


def main() -> int:
    carregar_env(RAIZ / ".env")
    try:
        config = ConfiguracaoIA.do_ambiente()
        if not config.gemini_configurado:
            print("Defina GEMINI_API_KEY e GEMINI_MODEL no arquivo .env (veja .env.example).")
            return 1
        provedor = ProvedorGemini(config)
        contexto = ContextoReacao(
            evento="convenceu", texto_alegacao="Meu cliente saiu do museu às 17h42, antes do fechamento.",
            classificacao=Classificacao.COERENTE, sucesso=True, codigos_motivo=("evidencia_relevante",),
            faixa_confianca="receptivo", nivel_suspeita="baixa", rodada=1,
            fatos_publicos=("O museu fecha às 18h.", "O registro da catraca mostra a saída às 17h42."))
        print(f"Modelo: {config.modelo_gemini}. Chamando o Gemini (limite de {config.timeout_segundos}s)...")
        reacao = provedor.gerar_reacao(JuizFormalista(), contexto)
        print(f"\n1) O juiz respondeu: {reacao.dialogo}")
        print(f"   Tokens: {reacao.tokens_entrada} de entrada e {reacao.tokens_saida} de saída.")
        pedido = ContextoInterpretacao(
            texto="A catraca mostra que ele saiu às 17h42, e o cofre só abre com a chave-mestra, que ele nunca teve.",
            afirmacoes_possiveis={
                "saiu_antes_do_fechamento": "O acusado saiu do museu antes das 18h.",
                "sem_chave_mestra": "O acusado nunca teve a chave-mestra que abriu o cofre.",
                "estava_em_casa": "O acusado passou a noite em casa."},
            provas_descobertas=(("E1", "Registro da catraca: saída às 17h42.", ("saiu_antes_do_fechamento",)),))
        print("\nInterpretando um argumento livre...")
        interpretacao = provedor.interpretar(pedido)
    except ObjectionException as erro:
        print(f"Falhou: {erro}")
        return 2
    print(f"2) Afirmações reconhecidas: {', '.join(interpretacao.afirmacoes) or 'nenhuma'} "
          f"(clareza {interpretacao.clareza}). Esperado: saiu_antes_do_fechamento e sem_chave_mestra.")
    print(f"   Tokens: {interpretacao.tokens_entrada} de entrada e {interpretacao.tokens_saida} de saída.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
