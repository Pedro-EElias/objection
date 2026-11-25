"""Demonstração de contas, perfis, energia de IA, ofertas e painel do administrador.

Uso (na raiz do projeto):  python scripts/demo_etapa2.py
Usa uma pasta temporária; não mexe na pasta data/.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from objection.casos.caso_1 import criar_caso as criar_caso_1
from objection.dominio.acao import Argumento, Blefe
from objection.dominio.juiz import JuizFormalista
from objection.excecoes import ObjectionException
from objection.game.motor_jogo import MotorJogo
from objection.persistencia.fabrica import criar_repositorios
from objection.servicos.administracao import ServicoAdministracao
from objection.servicos.autenticacao import ServicoAutenticacao
from objection.servicos.ofertas import ServicoOfertas, garantir_pacotes_padrao
from objection.servicos.tokens import ServicoTokens


def titulo(texto):
    print(f"\n--- {texto} ---")


def main():
    with tempfile.TemporaryDirectory() as pasta:
        repos = criar_repositorios(pasta)
        garantir_pacotes_padrao(repos)
        auth = ServicoAutenticacao(repos)
        tokens = ServicoTokens(repos)
        ofertas = ServicoOfertas(repos, tokens)
        adm = ServicoAdministracao(repos, tokens)
        caso, motor, juiz = criar_caso_1(), MotorJogo(semente=1), JuizFormalista()

        titulo("Contas")
        admin = auth.cadastrar_administrador("chefe", "Senha@123")
        ana = auth.cadastrar_jogador("ana", "Senha@123")
        print(f"{admin.apelido} ({admin.perfil}) e {ana.apelido} ({ana.perfil}, {ana.nivel.value})")

        titulo("Autorização por perfil: novato tenta blefar")
        partida = motor.iniciar_partida(caso, "p1", ana)
        motor.iniciar_julgamento(partida)
        try:
            motor.executar_acao(partida, caso, juiz, Blefe("b1", "Blefe", ["sem_chave_mestra"]), ana)
        except ObjectionException as erro:
            print(f"Barrado: {erro}")
        motor.executar_acao(partida, caso, juiz, Argumento("a1", "Saí cedo", ["saiu_antes_do_fechamento"]), ana)
        print("Argumento liberado para o novato.")

        titulo("Energia de IA (o jogador vê só a porcentagem)")
        print(f"Energia da {ana.apelido}: {tokens.energia(ana)}/100")
        for _ in range(3):
            texto = "Reação do juiz " * 200
            estimativa = 2 * tokens.estimar_tokens(texto)
            tokens.autorizar_chamada(ana, caso.id, estimativa)  # confere saldo e cota ANTES da chamada
            tokens.registrar_consumo(ana, caso.id, "augusto", "local", estimativa // 2, estimativa // 2, simulado=True)
        print(f"Depois de 3 chamadas simuladas: {tokens.energia(ana)}/100")

        titulo("Oferta simulada")
        print("Disponíveis:", [p.nome for p in ofertas.listar_disponiveis(ana)])
        ofertas.resgatar(ana, "boas-vindas")
        print(f"Resgatou boas-vindas. Energia: {tokens.energia(ana)}/100")
        try:
            ofertas.resgatar(ana, "boas-vindas")
        except ObjectionException as erro:
            print(f"Segunda tentativa: {erro}")

        titulo("Painel do administrador")
        resumo = adm.resumo_consumo(admin)
        print(f"Total {resumo['total']} tokens (real {resumo['real']}, simulado {resumo['simulado']})")
        print("Por conta:", resumo["por_conta"], "| por juiz:", resumo["por_juiz"])
        adm.definir_cota_por_caso(admin, ana.id, 1000)
        try:
            tokens.autorizar_chamada(ana, caso.id, 500)
        except ObjectionException as erro:
            print(f"Cota do caso reduzida para 1000 -> {erro}")
        adm.suspender_conta(admin, ana.id)
        try:
            motor.iniciar_partida(caso, "p2", auth.consultar(ana.id))
        except ObjectionException as erro:
            print(f"Conta suspensa: {erro}")


if __name__ == "__main__":
    main()
