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
