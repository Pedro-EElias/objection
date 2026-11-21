from objection.excecoes import DadosInvalidosException, EvidenciaInexistenteException
from objection.dominio.validacao import exigir_intervalo, exigir_texto


class Caso:
    """Ficha canônica de um caso: fatos, evidências e condições de vitória."""

    def __init__(
        self,
        id_caso,
        titulo,
        acusacao,
        dificuldade,
        fatos_canonicos,
        evidencias,
        testemunhas=(),
        pares_contraditorios=(),
        confianca_minima_vitoria=60,
        suspeita_maxima_vitoria=50,
    ):
        self._id = exigir_texto(id_caso, "id_caso")
        self._titulo = exigir_texto(titulo, "titulo")
        self._acusacao = exigir_texto(acusacao, "acusacao")
        self._dificuldade = exigir_intervalo(dificuldade, "dificuldade", 1, 5)
        self._fatos = tuple(fatos_canonicos)
        self._evidencias = {}
        for ev in evidencias:
            if ev.id in self._evidencias:
                raise DadosInvalidosException(f"Evidência duplicada: {ev.id}.")
            self._evidencias[ev.id] = ev
        self._testemunhas = tuple(testemunhas)
        self._pares = tuple(tuple(p) for p in pares_contraditorios)
        self._confianca_minima = exigir_intervalo(confianca_minima_vitoria, "confianca_minima_vitoria", 0, 100)
        self._suspeita_maxima = exigir_intervalo(suspeita_maxima_vitoria, "suspeita_maxima_vitoria", 0, 100)

    @property
    def id(self): return self._id

    @property
    def titulo(self): return self._titulo

    @property
    def acusacao(self): return self._acusacao

    @property
    def dificuldade(self): return self._dificuldade

    @property
    def fatos_canonicos(self): return self._fatos

    @property
    def testemunhas(self): return self._testemunhas

    @property
    def evidencias(self): return tuple(self._evidencias.values())

    @property
    def confianca_minima_vitoria(self): return self._confianca_minima

    @property
    def suspeita_maxima_vitoria(self): return self._suspeita_maxima

    def evidencia(self, id_evidencia) -> "Evidencia":
        try:
            return self._evidencias[id_evidencia]
        except KeyError:
            raise EvidenciaInexistenteException(
                f"A evidência '{id_evidencia}' não existe no caso '{self._id}'."
            ) from None

    def tem_testemunha(self, id_testemunha) -> bool:
        return id_testemunha in self._testemunhas

    def evidencias_que_sustentam(self, afirmacoes, descobertas) -> tuple:
        alvo = set(afirmacoes)
        return tuple(e.id for e in self._evidencias.values()
                     if e.id in descobertas and alvo & set(e.sustenta))

    def evidencias_que_refutam(self, afirmacoes, descobertas) -> tuple:
        alvo = set(afirmacoes)
        return tuple(e.id for e in self._evidencias.values()
                     if e.id in descobertas and alvo & set(e.refuta))

    def conflitos_com_declaracoes(self, afirmacoes, anteriores) -> int:
        novas, antigas = set(afirmacoes), set(anteriores)
        return sum(
            1 for a, b in self._pares
            if (a in novas and b in antigas) or (b in novas and a in antigas)
        )
