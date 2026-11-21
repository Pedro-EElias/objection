from objection.dominio.validacao import exigir_intervalo, exigir_texto


class Evidencia:
    """Elemento do caso. 'sustenta' e 'refuta' são etiquetas de afirmações."""

    def __init__(self, id_evidencia, descricao, confiabilidade, origem, sustenta=(), refuta=()):
        self._id = exigir_texto(id_evidencia, "id_evidencia")
        self._descricao = exigir_texto(descricao, "descricao")
        self._confiabilidade = exigir_intervalo(confiabilidade, "confiabilidade", 0, 100)
        self._origem = exigir_texto(origem, "origem")
        self._sustenta = tuple(sustenta)
        self._refuta = tuple(refuta)

    @property
    def id(self): return self._id

    @property
    def descricao(self): return self._descricao

    @property
    def confiabilidade(self): return self._confiabilidade

    @property
    def origem(self): return self._origem

    @property
    def sustenta(self): return self._sustenta

    @property
    def refuta(self): return self._refuta
