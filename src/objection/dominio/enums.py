from enum import Enum


class FasePartida(Enum):
    PREPARACAO = "preparacao"
    JULGAMENTO = "julgamento"
    DELIBERACAO = "deliberacao"
    ENCERRADA = "encerrada"
    ABANDONADA = "abandonada"


class Classificacao(Enum):
    COERENTE = "coerente"
    FRACO = "fraco"
    CONTRADITORIO = "contraditorio"
    SEM_EVIDENCIA = "sem_evidencia"


class TipoAlegacao(Enum):
    ARGUMENTO = "argumento"
    BLEFE = "blefe"
    SUBORNO = "suborno"


class FaixaConfianca(Enum):
    HOSTIL = "hostil"
    DESCONFIADO = "desconfiado"
    RECEPTIVO = "receptivo"
    CONVENCIDO = "convencido"


class ResultadoVeredito(Enum):
    FAVORAVEL = "favoravel"
    DESFAVORAVEL = "desfavoravel"
