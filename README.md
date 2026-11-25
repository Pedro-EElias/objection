# OBJECTION! — The Art of Deception

**Integrantes (nome e matrícula):** _preencher_
**Repositório:** _preencher o link_
**Disciplina:** Linguagem de Programação II (UFRN) — Atividade Unidade 03

Jogo narrativo de tribunal em Python. **A IA conversa; o motor do jogo decide.**

> Status: **Etapa 4** — o Caso 1 é jogável numa interface Flet, com partidas salvas em JSON (renomear, continuar, excluir), caderno de anotações e painel do administrador (consumo, contas, cotas e pacotes). Ainda não há IA real.

## Como executar

Requer Python 3.10+.

```bash
pip install -r requirements.txt     # Flet 1.1.2 (com a janela desktop) e pytest
python scripts/criar_admin.py       # cria o administrador (pede a senha no terminal)
python main.py                      # abre o jogo (use --web para abrir no navegador)
python -m pytest                    # roda os testes
python scripts/demo_terminal.py 42  # simula um julgamento com os 3 juízes (semente 42)
python scripts/demo_etapa2.py       # contas, perfis, energia, ofertas e painel do admin
```

## Estrutura

```
src/objection/
  excecoes.py        exceções personalizadas
  config.py          parâmetros de balanceamento (um só lugar)
  dominio/           Juiz (+3), AcaoJogo (+6), Usuario (Administrador, Jogador), Caso, Evidencia,
                     Partida, CarteiraTokens, RegistroConsumo, PacoteTokens, ResgateOferta, regras
  game/motor_jogo.py MotorJogo: única parte que altera o estado e emite o veredito
  persistencia/      Repositorio[T] (genérico) + RepositorioJson (backup, lock otimista)
  servicos/          autenticação, tokens, ofertas e administração
  casos/             Caso 1 (ficha canônica e opções) e catálogo
  ia/                ProvedorIA (abstrato) e ProvedorLocal (falas pré-escritas)
  app/controlador.py lógica de jogo da interface (sem código de tela, testável)
  ui/                tema, componentes e telas Flet
main.py              ponto de entrada
assets/              fontes (licença OFL) e, depois, retratos dos juízes
tests/               160 testes (regras, serviços, persistência e montagem das telas)
data/                criada ao rodar (arquivos JSON; fora do Git)
docs/DECISOES_TECNICAS.md
```

## Polimorfismo (até aqui)

1. `Juiz.avaliar()` — `JuizFormalista`, `JuizPragmatico`, `JuizCinico` aplicam regras diferentes à mesma análise.
2. `Usuario.pode()` — `Administrador` e `Jogador` (Novato/Veterano) respondem de formas diferentes.
3. `AcaoJogo.executar()` — `Investigacao`, `PrepararTestemunha`, `PrepararAlibi`, `TentativaSuborno`, `Argumento` e `Blefe` calculam efeitos diferentes.

## Pendente

Regras não implementadas, 5 situações de risco, diagrama UML e demais itens do enunciado serão completados nas etapas seguintes (ver `docs/DECISOES_TECNICAS.md`).
