# OBJECTION! — The Art of Deception

**Integrantes (nome e matrícula):** _preencher_
**Repositório:** _preencher o link_
**Disciplina:** Linguagem de Programação II (UFRN) — Atividade Unidade 03

Jogo narrativo de tribunal em Python. **A IA conversa; o motor do jogo decide.**

> Status: **Etapa 1 — núcleo do jogo** (domínio, regras, exceções e testes). Ainda não há interface, contas, persistência nem IA.

## Como executar

Requer Python 3.10+.

```bash
pip install -r requirements.txt     # só o pytest
python -m pytest                    # roda os testes
python scripts/demo_terminal.py 42  # simula um julgamento com os 3 juízes (semente 42)
```

## Estrutura

```
src/objection/
  excecoes.py        exceções personalizadas
  config.py          parâmetros de balanceamento (um só lugar)
  dominio/           Juiz (+3), AcaoJogo (+6), Caso, Evidencia, Partida, regras
  game/motor_jogo.py MotorJogo: única parte que altera o estado e emite o veredito
  casos/caso_1.py    rascunho do Caso 1
tests/               47 testes
docs/DECISOES_TECNICAS.md
```

## Polimorfismo (até aqui)

1. `Juiz.avaliar()` — `JuizFormalista`, `JuizPragmatico`, `JuizCinico` aplicam regras diferentes à mesma análise.
2. `AcaoJogo.executar()` — `Investigacao`, `PrepararTestemunha`, `PrepararAlibi`, `TentativaSuborno`, `Argumento` e `Blefe` calculam efeitos diferentes.

## Pendente

Regras não implementadas, 5 situações de risco, diagrama UML e demais itens do enunciado serão completados nas etapas seguintes (ver `docs/DECISOES_TECNICAS.md`).
