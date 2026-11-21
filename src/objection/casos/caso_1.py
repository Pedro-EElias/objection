"""RASCUNHO do Caso 1 (ficha canônica). O conteúdo final entra na Etapa 4."""
from objection.dominio.caso import Caso
from objection.dominio.evidencia import Evidencia


def criar_caso_1() -> Caso:
    return Caso(
        id_caso="caso-1",
        titulo="A Relíquia Desaparecida",
        acusacao="Furto de uma relíquia de uma instituição histórica.",
        dificuldade=1,
        fatos_canonicos=(
            "A instituição fecha às 18h.",
            "A relíquia estava num cofre aberto com chave-mestra.",
            "O acusado trabalha como restaurador.",
        ),
        evidencias=[
            Evidencia("E1", "Registro de acesso: cartão do acusado usado na saída às 17h42.",
                      90, "Controle de acesso", sustenta=("saiu_antes_do_fechamento",),
                      refuta=("ficou_apos_fechamento",)),
            Evidencia("E2", "Testemunha viu alguém de outra estatura no corredor às 22h.",
                      70, "Depoimento", sustenta=("outra_pessoa_no_corredor",)),
            Evidencia("E3", "O cofre foi aberto com chave-mestra, que o acusado nunca teve.",
                      85, "Perícia", sustenta=("sem_chave_mestra",)),
            Evidencia("E4", "Mensagem do acusado pedindo para ficar até mais tarde.",
                      80, "Comunicações", refuta=("saiu_antes_do_fechamento",)),
        ],
        testemunhas=("T1",),
        pares_contraditorios=(("saiu_antes_do_fechamento", "ficou_apos_fechamento"),),
    )
