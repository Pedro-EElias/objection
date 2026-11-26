import pytest

from objection.dominio.caso import Caso
from objection.dominio.evidencia import Evidencia
from objection.game.motor_jogo import MotorJogo


@pytest.fixture
def caso():
    return Caso(
        "C-TESTE", "Caso de teste", "Acusação fictícia", 1, ("Fato A",),
        [
            Evidencia("E1", "Registro de saída", 90, "Controle de acesso",
                      sustenta=("saiu_cedo",), refuta=("ficou_tarde",)),
            Evidencia("E2", "Testemunha no corredor", 70, "Depoimento",
                      sustenta=("outra_pessoa",)),
            Evidencia("E3", "Mensagem pedindo para ficar", 80, "Comunicações",
                      refuta=("saiu_cedo",)),
        ],
        testemunhas=("T1",),
        pares_contraditorios=(("saiu_cedo", "ficou_tarde"),),
    )


@pytest.fixture
def motor():
    return MotorJogo(semente=1)


@pytest.fixture
def partida(motor, caso):
    return motor.iniciar_partida(caso, "P1")


# ---------------------------------------------------------------- Etapa 2
from datetime import datetime, timedelta

from objection.dominio.usuario import Usuario
from objection.persistencia.fabrica import criar_repositorios
from objection.servicos.administracao import ServicoAdministracao
from objection.servicos.autenticacao import ServicoAutenticacao
from objection.servicos.ofertas import ServicoOfertas, garantir_pacotes_padrao
from objection.servicos.tokens import ServicoTokens


@pytest.fixture(autouse=True)
def hash_rapido(monkeypatch):
    """Menos iterações de PBKDF2 só nos testes, para ficarem rápidos."""
    monkeypatch.setattr(Usuario, "ITERACOES_HASH", 1000)


class Relogio:
    def __init__(self):
        self.agora = datetime(2026, 11, 20, 10, 0)

    def __call__(self):
        return self.agora

    def avancar_dias(self, n):
        self.agora += timedelta(days=n)


@pytest.fixture
def relogio():
    return Relogio()


@pytest.fixture
def repos(tmp_path):
    return criar_repositorios(tmp_path)


@pytest.fixture
def auth(repos, relogio):
    return ServicoAutenticacao(repos, relogio=relogio)


@pytest.fixture
def tokens(repos, relogio):
    return ServicoTokens(repos, relogio=relogio)


@pytest.fixture
def ofertas(repos, tokens, relogio):
    garantir_pacotes_padrao(repos)
    return ServicoOfertas(repos, tokens, relogio=relogio)


@pytest.fixture
def adm_srv(repos, tokens, relogio):
    return ServicoAdministracao(repos, tokens, relogio=relogio)


@pytest.fixture
def jogador(auth):
    return auth.cadastrar_jogador("ana", "Senha@123")


@pytest.fixture
def admin(auth):
    return auth.cadastrar_administrador("chefe", "Senha@123")


@pytest.fixture(autouse=True)
def sem_ia_no_ambiente(monkeypatch):
    """Os testes nunca devem usar chaves reais do ambiente de quem os executa."""
    for nome in ("GEMINI_API_KEY", "GEMINI_MODEL", "IA_TIMEOUT_SEGUNDOS", "IA_MAX_TOKENS_SAIDA", "IA_CADEIAS"):
        monkeypatch.delenv(nome, raising=False)
