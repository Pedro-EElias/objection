from objection.excecoes import DadosInvalidosException
from objection.ia.provedor_base import ProvedorIA, ReacaoJuiz

_OBJECAO = {"contradicao", "suborno_descoberto"}

_FALAS = {
    "formalista": {
        "abertura": ["Declaro aberta a sessão. A defesa terá a palavra, e esta corte exige precisão.",
                     "Sessão aberta. Cada afirmação será confrontada com os autos."],
        "convenceu": ["Os autos sustentam o que a defesa alega. Prossiga.",
                      "A cronologia é coerente. Anotado."],
        "nao_convenceu": ["Insuficiente. Esta corte não decide por impressões.",
                          "A alegação não encontra respaldo bastante. Prossiga, se houver mais."],
        "contradicao": ["A defesa afirma o contrário do que consta nos autos. Isso é grave.",
                        "Há contradição formal entre esta fala e o que já foi dito. Será registrado."],
        "sem_evidencia": ["Onde está a prova disso? Alegação sem prova nos autos não é argumento.",
                          "A defesa cita elementos que ainda não foram apresentados."],
        "suborno_ok": ["Esta corte nada viu, nada ouviu e nada registrou. Siga."],
        "suborno_descoberto": ["Tentativa de corromper o juízo. Isto consta dos autos, doutor.",
                               "Isso é uma ofensa a esta corte e será levado em conta."],
        "veredito_favoravel": ["Os fatos foram demonstrados. Absolvo o réu."],
        "veredito_desfavoravel": ["A defesa não demonstrou o que alegou. O réu é condenado."],
    },
    "pragmatico": {
        "abertura": ["Vamos ao que importa: o que aconteceu, e por que devo acreditar na sua versão?",
                     "Sessão aberta. Pode falar, mas fale de gente, não só de papel."],
        "convenceu": ["Isso faz sentido. Continue.",
                      "Plausível. Me dá um quadro mais claro do que houve."],
        "nao_convenceu": ["Não me convenceu. Falta o contexto que ligue as peças.",
                          "Bonito no papel, mas a vida real raramente acontece assim."],
        "contradicao": ["Isso não bate com o que a defesa já disse.",
                        "Essa versão briga com os fatos. Quer rever o que acabou de afirmar?"],
        "sem_evidencia": ["Você está ignorando um pedaço importante da história.",
                          "Falta chão nessa afirmação. Traga algo concreto."],
        "suborno_ok": ["Vou fingir que esta conversa não aconteceu."],
        "suborno_descoberto": ["Eu já vi muita coisa nesta sala, mas isso passou do limite.",
                               "Tentar me comprar foi um erro. Um erro caro."],
        "veredito_favoravel": ["Ouvi as duas versões, e a da defesa é a que se sustenta. Absolvido."],
        "veredito_desfavoravel": ["A versão da defesa não se sustentou. Lamento, mas é condenação."],
    },
    "cinico": {
        "abertura": ["Ah, mais uma defesa. Surpreenda-me, se for capaz.",
                     "Sessão aberta. Espero que o senhor tenha mais do que boa vontade."],
        "convenceu": ["Hm. Não foi ruim. Não se acostume.",
                      "Interessante. Quase me esqueci de ser desconfiado."],
        "nao_convenceu": ["Que ousadia... para tão pouco resultado.",
                          "Continue falando. Alguém precisa preencher o silêncio."],
        "contradicao": ["Que beleza: a defesa acaba de desmentir a si mesma.",
                        "Contradição! Raro ver alguém tropeçar com tanta convicção."],
        "sem_evidencia": ["Prova? Ou o senhor pretende que eu acredite por simpatia?",
                          "Citou algo que não existe nos autos. Corajoso."],
        "suborno_ok": ["Que gesto elegante. Pena que eu não vi nada."],
        "suborno_descoberto": ["Tentou me comprar? Com isso? Fico até ofendido pelo preço.",
                               "Suborno, e mal feito. Os autos agradecem."],
        "veredito_favoravel": ["Para minha própria surpresa, a defesa me convenceu. Absolvido."],
        "veredito_desfavoravel": ["Como esperado: condenado. Foi um prazer desconfiar."],
    },
}


class ProvedorLocal(ProvedorIA):
    """Falas pré-escritas por juiz. Funciona sem internet e é o fallback de qualquer IA."""

    nome = "local"

    def gerar_reacao(self, juiz, evento, indice=0):
        falas = _FALAS.get(juiz.id, {}).get(evento)
        if not falas:
            raise DadosInvalidosException(f"Sem fala para o juiz '{juiz.id}' no evento '{evento}'.")
        return ReacaoJuiz(falas[indice % len(falas)], evento in _OBJECAO)
