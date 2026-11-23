import pytest

from objection.dominio.tokens import PacoteTokens
from objection.dominio.usuario import Jogador
from objection.excecoes import DadosCorrompidosException, VersaoConflitanteException
from objection.persistencia.fabrica import criar_repositorios


def test_dados_sao_carregados_ao_iniciar(tmp_path):
    r1 = criar_repositorios(tmp_path)
    r1.usuarios.salvar(Jogador.novo("j1", "ana", "senha123"))
    r1.pacotes.salvar(PacoteTokens("p1", "Pacote", 100, limite_por_conta=2))
    r2 = criar_repositorios(tmp_path)  # "reabrir o programa"
    assert r2.usuarios.buscar_por_id("j1").verificar_senha("senha123")
    assert r2.pacotes.buscar_por_id("p1").limite_por_conta == 2  # dois tipos no mesmo repositório genérico


def test_remocao_persiste(tmp_path):
    r1 = criar_repositorios(tmp_path)
    r1.usuarios.salvar(Jogador.novo("j1", "ana", "senha123"))
    assert r1.usuarios.remover("j1") is True
    assert criar_repositorios(tmp_path).usuarios.listar() == []
    assert r1.usuarios.remover("j1") is False


def test_lock_otimista_recusa_gravacao_sobre_versao_antiga(tmp_path):
    base = criar_repositorios(tmp_path)
    base.pacotes.salvar(PacoteTokens("p1", "Pacote", 100))
    janela_a, janela_b = criar_repositorios(tmp_path), criar_repositorios(tmp_path)
    a = janela_a.pacotes.buscar_por_id("p1")
    b = janela_b.pacotes.buscar_por_id("p1")
    a.alterar(tokens=200)
    janela_a.pacotes.salvar(a)
    b.alterar(tokens=300)
    with pytest.raises(VersaoConflitanteException):
        janela_b.pacotes.salvar(b)
    janela_b.pacotes.recarregar()
    assert janela_b.pacotes.buscar_por_id("p1").tokens == 200  # vale a primeira gravação


def test_id_novo_criado_por_outra_instancia_tambem_conflita(tmp_path):
    a, b = criar_repositorios(tmp_path), criar_repositorios(tmp_path)
    a.pacotes.salvar(PacoteTokens("p1", "A", 100))
    with pytest.raises(VersaoConflitanteException):
        b.pacotes.salvar(PacoteTokens("p1", "B", 100))


def test_json_corrompido_e_recuperado_da_copia_de_seguranca(tmp_path):
    r = criar_repositorios(tmp_path)
    r.pacotes.salvar(PacoteTokens("p1", "Pacote", 100))
    r.pacotes.salvar(PacoteTokens("p2", "Outro", 200))  # cria o .bak com p1
    (tmp_path / "pacotes.json").write_text("{ isto não é json", encoding="utf-8")
    novo = criar_repositorios(tmp_path)
    assert novo.pacotes.buscar_por_id("p1") is not None


def test_json_corrompido_sem_copia_levanta_excecao(tmp_path):
    (tmp_path / "pacotes.json").write_text("lixo", encoding="utf-8")
    with pytest.raises(DadosCorrompidosException):
        criar_repositorios(tmp_path)


def test_estrutura_invalida_e_tratada_como_corrompida(tmp_path):
    (tmp_path / "usuarios.json").write_text('{"registros": {"x": {"versao": 1, "dados": {"tipo": "?"}}}}',
                                            encoding="utf-8")
    with pytest.raises(DadosCorrompidosException):
        criar_repositorios(tmp_path)
