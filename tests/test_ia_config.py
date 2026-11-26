import pytest

from objection.excecoes import ConfiguracaoIAException
from objection.ia.configuracao import CADEIAS_PADRAO, ConfiguracaoIA, carregar_env


def test_padroes_sem_variaveis():
    c = ConfiguracaoIA.do_ambiente({})
    assert not c.gemini_configurado and c.timeout_segundos == 8.0 and c.max_tokens_saida == 512
    assert c.cadeias["formalista"] == ("gemini", "local") and c.cadeias["cinico"] == ("local",)


def test_gemini_so_conta_como_configurado_com_chave_e_modelo():
    assert not ConfiguracaoIA.do_ambiente({"GEMINI_API_KEY": "k"}).gemini_configurado
    assert not ConfiguracaoIA.do_ambiente({"GEMINI_MODEL": "m"}).gemini_configurado
    assert ConfiguracaoIA.do_ambiente({"GEMINI_API_KEY": "k", "GEMINI_MODEL": "m"}).gemini_configurado


def test_repr_nao_mostra_a_chave():
    c = ConfiguracaoIA.do_ambiente({"GEMINI_API_KEY": "segredo-super-secreto", "GEMINI_MODEL": "m"})
    assert "segredo" not in repr(c) and "segredo" not in str(c)


@pytest.mark.parametrize("nome,valor", [("IA_TIMEOUT_SEGUNDOS", "abc"), ("IA_TIMEOUT_SEGUNDOS", "0"),
                                        ("IA_TIMEOUT_SEGUNDOS", "999"), ("IA_MAX_TOKENS_SAIDA", "10"),
                                        ("IA_MAX_TOKENS_SAIDA", "x")])
def test_numeros_invalidos_levantam_erro_com_o_nome_da_variavel(nome, valor):
    with pytest.raises(ConfiguracaoIAException) as erro:
        ConfiguracaoIA.do_ambiente({nome: valor})
    assert nome in str(erro.value)


def test_cadeias_por_variavel_e_local_sempre_no_fim():
    c = ConfiguracaoIA.do_ambiente({"IA_CADEIAS": "formalista:gemini;pragmatico:groq,gemini"})
    assert c.cadeias["formalista"] == ("gemini", "local")
    assert c.cadeias["pragmatico"] == ("groq", "gemini", "local")
    assert c.cadeias["cinico"] == CADEIAS_PADRAO["cinico"]


@pytest.mark.parametrize("bruto", ["juiz_x:gemini", "formalista:openai", "formalista:", "semdoispontos"])
def test_cadeias_invalidas(bruto):
    with pytest.raises(ConfiguracaoIAException):
        ConfiguracaoIA.do_ambiente({"IA_CADEIAS": bruto})


def test_carregar_env_le_sem_sobrescrever(tmp_path):
    arquivo = tmp_path / ".env"
    arquivo.write_text('# comentário\n\nGEMINI_API_KEY="abc"\nGEMINI_MODEL=modelo-x\nVAZIA=\nJA_EXISTE=novo\n',
                       encoding="utf-8")
    env = {"JA_EXISTE": "antigo"}
    assert carregar_env(arquivo, env) == 2
    assert env == {"JA_EXISTE": "antigo", "GEMINI_API_KEY": "abc", "GEMINI_MODEL": "modelo-x"}


def test_carregar_env_sem_arquivo(tmp_path):
    assert carregar_env(tmp_path / "nao-existe", {}) == 0
