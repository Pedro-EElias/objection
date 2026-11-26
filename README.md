# OBJECTION! — The Art of Deception

**Integrantes (nome e matrícula):** _preencher_
**Repositório:** _preencher o link_
**Disciplina:** Linguagem de Programação II (UFRN) — Atividade Unidade 03

Jogo narrativo de tribunal em Python. **A IA conversa; o motor do jogo decide.**

> Status: **Etapa 5** — o Caso 1 é jogável numa interface Flet, com partidas salvas em JSON (renomear, continuar, excluir), caderno de anotações e painel do administrador (consumo, contas, cotas e pacotes). A IA do juiz Augusto (Gemini) é opcional e cai nas falas pré-escritas se falhar.

## Como executar

Requer Python 3.10+.

```bash
pip install -r requirements.txt     # Flet 1.1.2 (com a janela desktop) e pytest
python scripts/criar_admin.py       # cria o administrador (pede a senha no terminal)
python main.py                      # abre o jogo (use --web para abrir no navegador)
python scripts/testar_gemini.py     # 1 chamada real ao Gemini, para validar chave e modelo (opcional)
python scripts/promover_veterano.py apelido   # demonstração: libera blefe, suborno e fala livre
python -m pytest                    # roda os testes
python scripts/demo_terminal.py 42  # simula um julgamento com os 3 juízes (semente 42)
python scripts/demo_etapa2.py       # contas, perfis, energia, ofertas e painel do admin
```

## IA do juiz (opcional)

Sem configurar nada, o jogo é completo, com falas pré-escritas. Para ligar o Gemini no juiz Augusto Valença:

1. Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY` e `GEMINI_MODEL` (o nome do modelo vem da documentação atual do Google AI Studio; ele não fica fixo no código).
2. Rode `python scripts/testar_gemini.py` para conferir.
3. Na partida com o Augusto, ligue **Juiz com IA (online)**. O Veterano ganha a caixa **Argumento livre**: escreve com as próprias palavras, usando as provas que descobriu.

A IA escreve a fala do juiz e, para o Veterano, **interpreta o argumento livre** (quais afirmações do caso ele fez). Confiança, suspeita, créditos, provas e veredito são calculados pelo motor, que valida tudo o que a IA devolve. Se a IA falhar, demorar, responder fora do formato ou a energia acabar, o jogo continua com as falas locais. O `.env` nunca vai para o Git.

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
  ia/                ProvedorIA (abstrato), ProvedorLocal, ProvedorGemini, contrato da resposta,
                     defesa contra prompt injection e ServicoDialogo (cadeia de provedores + fallback)
  app/controlador.py lógica de jogo da interface (sem código de tela, testável)
  ui/                tema, componentes e telas Flet
main.py              ponto de entrada
assets/              fontes (licença OFL) e, depois, retratos dos juízes
tests/               325 testes (regras, serviços, persistência, IA com respostas simuladas e telas)
data/                criada ao rodar (arquivos JSON; fora do Git)
docs/DECISOES_TECNICAS.md
```

## Polimorfismo (até aqui)

1. `Juiz.avaliar()` — `JuizFormalista`, `JuizPragmatico`, `JuizCinico` aplicam regras diferentes à mesma análise.
2. `Usuario.pode()` — `Administrador` e `Jogador` (Novato/Veterano) respondem de formas diferentes.
3. `AcaoJogo.executar()` — `Investigacao`, `PrepararTestemunha`, `PrepararAlibi`, `TentativaSuborno`, `Argumento` e `Blefe` calculam efeitos diferentes.

## Pendente

Regras não implementadas, 5 situações de risco, diagrama UML e demais itens do enunciado serão completados nas etapas seguintes (ver `docs/DECISOES_TECNICAS.md`).
