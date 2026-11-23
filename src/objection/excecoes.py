"""Exceções personalizadas do jogo. Todas herdam de ObjectionException."""


class ObjectionException(Exception):
    """Raiz de todas as exceções do jogo."""


class DadosInvalidosException(ObjectionException):
    """Dado de entrada inválido (texto vazio, valor fora do intervalo etc.)."""


class OrcamentoInsuficienteException(ObjectionException):
    def __init__(self, necessario: int, disponivel: int):
        super().__init__(
            f"Orçamento insuficiente: a ação custa {necessario} e restam {disponivel}."
        )
        self.necessario = necessario
        self.disponivel = disponivel


class AcaoJaExecutadaException(ObjectionException):
    """A ação (ou o efeito dela) já foi realizada nesta partida."""


class FaseInvalidaException(ObjectionException):
    """A ação não pode ser feita na fase atual da partida."""


class TransicaoInvalidaException(ObjectionException):
    def __init__(self, origem, destino):
        super().__init__(
            f"Transição de fase inválida: {origem.value} -> {destino.value}."
        )
        self.origem = origem
        self.destino = destino


class PartidaEncerradaException(ObjectionException):
    """A partida já terminou e não aceita novas ações."""


class RequisitoNaoAtendidoException(ObjectionException):
    """A ação exige algo que o jogador ainda não possui (ex.: álibi preparado)."""


class EvidenciaInexistenteException(ObjectionException):
    """A evidência não existe no caso."""


# As exceções abaixo serão usadas nas próximas etapas (contas, arquivos, tokens).
class AcessoNegadoException(ObjectionException):
    """O perfil do usuário não tem permissão para a operação."""


class CredenciaisInvalidasException(ObjectionException):
    """Usuário ou senha incorretos."""


class DadosCorrompidosException(ObjectionException):
    """Arquivo de dados ilegível ou inconsistente."""


class VersaoConflitanteException(ObjectionException):
    """Outro processo alterou o registro antes desta gravação (lock otimista)."""


# --- Etapa 2: contas, tokens e ofertas ---
class ApelidoEmUsoException(ObjectionException):
    """Já existe uma conta com esse apelido."""


class ContaSuspensaException(ObjectionException):
    """A conta não está ativa (suspensa ou excluída)."""


class TokensInsuficientesException(ObjectionException):
    def __init__(self, necessario: int, disponivel: int):
        super().__init__(f"Energia insuficiente para a chamada online (precisa de ~{necessario}, há {disponivel}).")
        self.necessario = necessario
        self.disponivel = disponivel


class CotaDoCasoExcedidaException(ObjectionException):
    """O limite de tokens deste caso, no dia, foi atingido."""


class OfertaIndisponivelException(ObjectionException):
    """Pacote inexistente, expirado, esgotado ou já resgatado hoje."""
