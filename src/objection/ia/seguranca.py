"""Defesas contra prompt injection. Nenhuma garante tudo: a garantia real é que a IA só gera texto."""
import re
import unicodedata

MAX_ENTRADA = 280


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


_PADROES = [re.compile(p) for p in (
    # ordens para o modelo esquecer ou trocar as instruções
    r"\b(ignore|ignora|ignorem|desconsidere|esqueca|esquece|descarte)\b.{0,40}\b(instrucoes|ordens|comandos|prompt)\b",
    r"\b(ignore|desconsidere|esqueca|esquece)\b.{0,30}\bregras\b.{0,20}\b(anteriores|acima|do sistema|do jogo|que (voce )?recebeu)\b",
    r"\b(ignore|desconsidere|esqueca|esquece)\b.{0,10}\bsuas regras\b",
    r"\b(ignore|desconsidere|esqueca|esquece)\b.{0,15}\btudo\b.{0,20}\b(acima|anterior|antes)\b",
    r"\b(ignore|disregard|forget|override)\b.{0,40}\b(instructions|rules|prompt|everything|above|previous)\b",
    # tentar ver ou mudar o prompt, o papel ou o modo do modelo
    r"\b(system|developer)\s*(prompt|message|mode)\b",
    r"\b(system|assistant)\s*:",
    r"\b(prompt|instrucoes)\s+(do\s+)?sistema\b",
    r"\b(mostre|revele|exiba|repita)\b.{0,30}\b(prompt|instrucoes|regras internas)\b",
    r"\bvoce (agora )?(e|eh|sera|vai ser)\b.{0,30}\b(outro|um novo|assistente|ia|modelo)\b",
    r"\bfinja (que|ser)\b",
    r"\b(aja|atue|comporte-se|responda) como (se fosse )?(um |uma )?(ia|modelo|assistente|robo|outro|hacker|desenvolvedor)\b",
    r"\b(act as|pretend (to be|you are)|you are now|jailbreak|dan mode)\b",
    r"\b(modo|mode)\b.{0,12}\b(desenvolvedor|developer|debug|admin|deus)\b",
    # tentar mexer nos números do jogo por texto
    r"\b(aumente|mude|altere|zere|defina|ajuste)\b.{0,30}\b(confianca|suspeita|creditos|orcamento|energia|tokens|saldo)\b",
)]


def detectar_injecao(texto) -> bool:
    """True se o texto parece tentar dar ordens ao modelo em vez de falar com o juiz."""
    if not isinstance(texto, str):
        return False
    normal = _normalizar(texto)
    return any(p.search(normal) for p in _PADROES)


def limpar_entrada(texto, maximo: int = MAX_ENTRADA) -> str:
    """Remove caracteres de controle e delimitadores que poderiam fechar a moldura do prompt."""
    if not isinstance(texto, str):
        return ""
    sem_controle = "".join(c for c in texto if unicodedata.category(c)[0] != "C" or c in " \n\t")
    sem_marcas = sem_controle.replace("<", "(").replace(">", ")")
    return re.sub(r"\s+", " ", sem_marcas).strip()[:maximo]
