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


class StatusConta(Enum):
    ATIVA = "ativa"
    SUSPENSA = "suspensa"
    EXCLUIDA = "excluida"


class NivelJogador(Enum):
    NOVATO = "novato"
    VETERANO = "veterano"


class Permissao(Enum):
    JOGAR = "jogar"
    RESGATAR_OFERTAS = "resgatar_ofertas"
    USAR_BLEFE = "usar_blefe"
    USAR_SUBORNO = "usar_suborno"
    ARGUMENTO_LIVRE = "argumento_livre"
    USAR_CADERNO = "usar_caderno"
    VER_CONSUMO = "ver_consumo"
    GERENCIAR_COTAS = "gerenciar_cotas"
    GERENCIAR_CONTAS = "gerenciar_contas"
    GERENCIAR_PACOTES = "gerenciar_pacotes"
