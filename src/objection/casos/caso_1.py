"""Caso 1: A Relíquia Desaparecida. Ficha canônica e opções do jogador."""
from objection.dominio.acao import (
    Argumento, Blefe, Investigacao, PrepararAlibi, PrepararTestemunha, TentativaSuborno,
)
from objection.dominio.caso import Caso
from objection.dominio.evidencia import Evidencia

ID = "caso-1"
SINOPSE = (
    "Caio Mendes, restaurador do Museu da Ordem, é acusado de furtar o Cálice de Prata do "
    "cofre do segundo andar. O museu fecha às 18h e o sumiço foi notado às 7h da manhã seguinte."
)


def criar_caso() -> Caso:
    return Caso(
        id_caso=ID,
        titulo="A Relíquia Desaparecida",
        acusacao="Furto do Cálice de Prata, relíquia do Museu da Ordem.",
        dificuldade=1,
        fatos_canonicos=(
            "O museu fecha às 18h.",
            "O Cálice de Prata ficava num cofre do segundo andar.",
            "O sumiço foi notado às 7h da manhã seguinte.",
            "Caio Mendes é restaurador e trabalha com a peça.",
        ),
        evidencias=[
            Evidencia("E1", "Registro da catraca: o cartão de Caio foi usado na saída às 17h42.",
                      90, "Controle de acesso",
                      sustenta=("saiu_antes_do_fechamento", "estava_em_casa"),
                      refuta=("ficou_apos_fechamento", "catraca_com_defeito")),
            Evidencia("E2", "Depoimento: alguém de estatura diferente da de Caio andava pelo corredor às 22h.",
                      70, "Depoimento", sustenta=("outra_pessoa_no_corredor",)),
            Evidencia("E3", "Perícia: o cofre foi aberto com a chave-mestra, que Caio nunca teve.",
                      85, "Perícia", sustenta=("sem_chave_mestra", "seguranca_tinha_chave")),
            Evidencia("E4", "Mensagem de Caio à chefe: \"Posso ficar até mais tarde hoje?\"",
                      80, "Comunicações", refuta=("saiu_antes_do_fechamento",)),
        ],
        testemunhas=("T1",),
        pares_contraditorios=(
            ("saiu_antes_do_fechamento", "ficou_apos_fechamento"),
            ("estava_em_casa", "ficou_apos_fechamento"),
        ),
    )


def criar_opcoes() -> list:
    return [
        # Preparação
        Investigacao("i-catraca", "Pedir o registro da catraca do museu", "E1"),
        Investigacao("i-pericia", "Pedir a perícia do cofre", "E3"),
        Investigacao("i-corredor", "Tomar o depoimento sobre o corredor", "E2"),
        Investigacao("i-mensagens", "Examinar as mensagens do cliente", "E4"),
        PrepararTestemunha("t-corredor", "Preparar a testemunha do corredor para depor", "T1"),
        PrepararAlibi("al-casa", "Montar um álibi: Caio estava em casa à noite", "estava_em_casa"),
        TentativaSuborno("su-discreto", "Fazer uma oferta discreta ao juiz", nivel_discricao=2),
        # Julgamento: argumentos
        Argumento("ar-saida", "Meu cliente saiu do museu às 17h42, antes do fechamento.",
                  ["saiu_antes_do_fechamento"], ["E1"]),
        Argumento("ar-chave", "O cofre foi aberto com a chave-mestra, que meu cliente nunca teve.",
                  ["sem_chave_mestra"], ["E3"]),
        Argumento("ar-corredor", "Uma testemunha viu outra pessoa no corredor às 22h.",
                  ["outra_pessoa_no_corredor"], ["E2"]),
        Argumento("ar-oficio", "Meu cliente restaura a peça todos os dias; não precisaria roubá-la.",
                  ["tem_acesso_legitimo"]),
        Argumento("ar-carater", "Meu cliente jamais faria uma coisa dessas.",
                  ["inocencia_geral"]),
        # Julgamento: blefes
        Blefe("bl-catraca", "A catraca estava com defeito naquela semana.",
              ["catraca_com_defeito"], nivel=1),
        Blefe("bl-seguranca", "O segurança da noite também tinha a chave-mestra.",
              ["seguranca_tinha_chave"], nivel=2),
        Blefe("bl-casa", "Meu cliente passou a noite inteira em casa, com testemunhas.",
              ["estava_em_casa"], nivel=3),
    ]
