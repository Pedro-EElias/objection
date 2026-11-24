"""Demonstração em terminal do núcleo do jogo (sem interface e sem IA).

Uso (na raiz do projeto):  python scripts/demo_terminal.py [semente]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from objection.casos.caso_1 import criar_caso as criar_caso_1
from objection.dominio.acao import Argumento, Blefe, Investigacao, PrepararTestemunha
from objection.dominio.juiz import JuizCinico, JuizFormalista, JuizPragmatico
from objection.game.motor_jogo import MotorJogo


def mostrar(partida, titulo, r):
    print(f"\n> {titulo}")
    print(f"  {'SUCESSO' if r.sucesso else 'FALHA'} | confiança {partida.confianca} | "
          f"suspeita {partida.suspeita} | créditos {partida.orcamento}")
    for m in r.motivos:
        print(f"    - {m}")


def jogar(juiz, semente):
    caso = criar_caso_1()
    motor = MotorJogo(semente=semente)
    p = motor.iniciar_partida(caso, "demo")
    print(f"\n{'=' * 60}\n{caso.titulo} | {juiz.nome} ({type(juiz).__name__})\n{'=' * 60}")
    plano = [
        Investigacao("i1", "Investigar o registro de acesso", "E1"),
        Investigacao("i2", "Investigar a perícia do cofre", "E3"),
        PrepararTestemunha("t1", "Preparar a testemunha do corredor", "T1"),
    ]
    for acao in plano:
        mostrar(p, acao.texto, motor.executar_acao(p, caso, juiz, acao))
    motor.iniciar_julgamento(p)
    plano = [
        Argumento("a1", "Meu cliente saiu antes do fechamento", ["saiu_antes_do_fechamento"], ["E1"]),
        Blefe("b1", "Outra pessoa tinha a chave-mestra", ["sem_chave_mestra", "outra_pessoa_no_corredor"],
              nivel=2, evidencias_citadas=["E3"]),
    ]
    for acao in plano:
        mostrar(p, acao.texto, motor.executar_acao(p, caso, juiz, acao))
    v = motor.emitir_veredito(p, caso)
    print(f"\nVEREDITO: {v.resultado.value.upper()} (faixa final: {v.faixa.value})")
    for m in v.motivos:
        print(f"  - {m}")


if __name__ == "__main__":
    semente = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    for juiz in (JuizFormalista(), JuizPragmatico(), JuizCinico()):
        jogar(juiz, semente)
