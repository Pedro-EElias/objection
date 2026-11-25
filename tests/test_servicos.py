import pytest

from objection.dominio.enums import NivelJogador, StatusConta
from objection.excecoes import (
    AcessoNegadoException, ApelidoEmUsoException, ContaSuspensaException,
    CredenciaisInvalidasException, DadosInvalidosException, OfertaIndisponivelException,
    TokensInsuficientesException,
)
from objection.persistencia.fabrica import criar_repositorios


# ------------------------------------------------------------- autenticação
def test_cadastro_cria_jogador_novato_e_carteira(auth, repos):
    j = auth.cadastrar_jogador("ana", "Senha@123")
    assert j.nivel is NivelJogador.NOVATO
    assert repos.carteiras.buscar_por_id(j.id) is not None


def test_apelido_unico_sem_diferenciar_maiusculas(auth):
    auth.cadastrar_jogador("ana", "Senha@123")
    with pytest.raises(ApelidoEmUsoException):
        auth.cadastrar_jogador("ANA", "Senha@123")


def test_login_e_erros_com_a_mesma_mensagem(auth, jogador):
    assert auth.login("ANA", "Senha@123").id == jogador.id
    with pytest.raises(CredenciaisInvalidasException) as e1:
        auth.login("ana", "errada")
    with pytest.raises(CredenciaisInvalidasException) as e2:
        auth.login("fantasma", "Senha@123")
    assert str(e1.value) == str(e2.value)


def test_alterar_senha_exige_a_atual(auth, jogador):
    with pytest.raises(CredenciaisInvalidasException):
        auth.alterar_senha(jogador, "errada", "Nova@senha1")
    auth.alterar_senha(jogador, "Senha@123", "Nova@senha1")
    assert auth.login("ana", "Nova@senha1")


def test_alterar_apelido_respeita_unicidade(auth, jogador):
    auth.cadastrar_jogador("bia", "Senha@123")
    with pytest.raises(ApelidoEmUsoException):
        auth.alterar_apelido(jogador, "bia")
    auth.alterar_apelido(jogador, "ana2")
    assert auth.login("ana2", "Senha@123")


def test_excluir_conta_remove_usuario_e_carteira(auth, jogador, repos):
    with pytest.raises(CredenciaisInvalidasException):
        auth.excluir_conta(jogador, "errada")
    auth.excluir_conta(jogador, "Senha@123")
    assert repos.usuarios.buscar_por_id(jogador.id) is None
    assert repos.carteiras.buscar_por_id(jogador.id) is None
    with pytest.raises(CredenciaisInvalidasException):
        auth.login("ana", "Senha@123")


# ------------------------------------------------------------------- tokens
def test_energia_comeca_cheia_e_cai_com_o_consumo(tokens, jogador):
    assert tokens.energia(jogador) == 100
    tokens.registrar_consumo(jogador, "caso-1", "augusto", "gemini", 400, 400)
    assert tokens.energia(jogador) == 90  # 800 de 8000


def test_consumo_vai_para_o_livro_e_marca_simulado(tokens, jogador, repos):
    r = tokens.registrar_consumo(jogador, "caso-1", "augusto", "local", 50, 50, simulado=True)
    assert r.total == 100 and r.simulado
    assert len(repos.consumos.listar()) == 1


def test_recarga_no_dia_seguinte(tokens, jogador, relogio):
    tokens.registrar_consumo(jogador, "caso-1", "augusto", "gemini", 2000, 2000)
    assert tokens.energia(jogador) == 50
    relogio.avancar_dias(1)
    assert tokens.energia(jogador) == 100


def test_chamada_online_e_barrada_sem_saldo(tokens, jogador):
    tokens.registrar_consumo(jogador, "caso-1", "augusto", "gemini", 4000, 3800)
    with pytest.raises(TokensInsuficientesException):
        tokens.autorizar_chamada(jogador, "caso-2", 500)


def test_conta_suspensa_nao_usa_ia(tokens, jogador):
    jogador.suspender()
    with pytest.raises(ContaSuspensaException):
        tokens.autorizar_chamada(jogador, "caso-1", 10)


def test_conflito_de_versao_na_carteira_e_resolvido_com_nova_tentativa(tokens, jogador, tmp_path):
    outra_janela = criar_repositorios(tmp_path)
    c = outra_janela.carteiras.buscar_por_id(jogador.id)
    c.creditar(100)
    outra_janela.carteiras.salvar(c)
    tokens.registrar_consumo(jogador, "caso-1", "augusto", "gemini", 50, 50)
    assert tokens.carteira_atual(jogador.id).saldo == 8000 + 100 - 100


def test_estimativa_de_tokens():
    from objection.servicos.tokens import ServicoTokens
    assert ServicoTokens.estimar_tokens("a" * 400) == 100
    assert ServicoTokens.estimar_tokens("") == 1


# ------------------------------------------------------------------- ofertas
def test_boas_vindas_so_uma_vez(ofertas, tokens, jogador):
    ofertas.resgatar(jogador, "boas-vindas")
    assert tokens.carteira_atual(jogador.id).saldo == 8000 + 4000
    with pytest.raises(OfertaIndisponivelException):
        ofertas.resgatar(jogador, "boas-vindas")


def test_recompensa_diaria_uma_por_dia(ofertas, jogador, relogio):
    ofertas.resgatar(jogador, "diaria")
    with pytest.raises(OfertaIndisponivelException):
        ofertas.resgatar(jogador, "diaria")
    relogio.avancar_dias(1)
    ofertas.resgatar(jogador, "diaria")


def test_pacote_promocional_tem_limite_por_conta(ofertas, jogador):
    for _ in range(3):
        ofertas.resgatar(jogador, "promocional")
    with pytest.raises(OfertaIndisponivelException):
        ofertas.resgatar(jogador, "promocional")


def test_oferta_expirada_ou_inexistente(ofertas, adm_srv, admin, jogador, relogio):
    from datetime import date
    p = adm_srv.criar_pacote(admin, "Relâmpago", 100, validade_ate=date(2026, 11, 20))
    ofertas.resgatar(jogador, p.id)
    relogio.avancar_dias(1)
    with pytest.raises(OfertaIndisponivelException):
        ofertas.resgatar(jogador, p.id)
    with pytest.raises(OfertaIndisponivelException):
        ofertas.resgatar(jogador, "nao-existe")


def test_listar_disponiveis_esconde_o_que_ja_foi_usado(ofertas, jogador):
    ofertas.resgatar(jogador, "boas-vindas")
    nomes = {p.id for p in ofertas.listar_disponiveis(jogador)}
    assert "boas-vindas" not in nomes and "diaria" in nomes


def test_administrador_nao_resgata_oferta(ofertas, admin):
    with pytest.raises(AcessoNegadoException):
        ofertas.resgatar(admin, "diaria")


# ----------------------------------------------------------- administração
def test_resumo_de_consumo(adm_srv, tokens, auth, jogador, admin):
    outra = auth.cadastrar_jogador("bia", "Senha@123")
    tokens.registrar_consumo(jogador, "caso-1", "augusto", "gemini", 100, 100)
    tokens.registrar_consumo(outra, "caso-2", "helena", "local", 30, 30, simulado=True)
    r = adm_srv.resumo_consumo(admin)
    assert r["total"] == 260 and r["simulado"] == 60 and r["real"] == 200
    assert r["por_conta"] == {"ana": 200, "bia": 60}
    assert r["por_caso"] == {"caso-1": 200, "caso-2": 60}
    assert r["por_juiz"]["augusto"] == 200 and r["por_provedor"]["local"] == 60


def test_jogador_nao_usa_funcoes_de_administrador(adm_srv, jogador):
    with pytest.raises(AcessoNegadoException):
        adm_srv.resumo_consumo(jogador)
    with pytest.raises(AcessoNegadoException):
        adm_srv.definir_cota_diaria(jogador, jogador.id, 99999)
    with pytest.raises(AcessoNegadoException):
        adm_srv.suspender_conta(jogador, jogador.id)
    with pytest.raises(AcessoNegadoException):
        adm_srv.criar_pacote(jogador, "x", 100)


def test_admin_define_cotas_e_concede_ou_revoga_tokens(adm_srv, admin, jogador, tokens):
    adm_srv.definir_cota_diaria(admin, jogador.id, 10_000)
    adm_srv.definir_cota_por_caso(admin, jogador.id, 2000)
    c = tokens.carteira_atual(jogador.id)
    assert (c.cota_diaria, c.cota_por_caso) == (10_000, 2000)
    adm_srv.conceder_tokens(admin, jogador.id, 500)
    assert tokens.carteira_atual(jogador.id).saldo == 8000 + 500
    adm_srv.revogar_tokens(admin, jogador.id, 99_999)
    assert tokens.carteira_atual(jogador.id).saldo == 0


def test_admin_suspende_e_reativa_jogador(adm_srv, admin, jogador, auth):
    adm_srv.suspender_conta(admin, jogador.id)
    assert auth.consultar(jogador.id).status is StatusConta.SUSPENSA
    adm_srv.reativar_conta(admin, jogador.id)
    assert auth.consultar(jogador.id).status is StatusConta.ATIVA


def test_admin_nao_gerencia_contas_de_administrador(adm_srv, admin):
    with pytest.raises(DadosInvalidosException):
        adm_srv.suspender_conta(admin, admin.id)


def test_admin_remove_conta_de_jogador(adm_srv, admin, jogador, repos):
    adm_srv.remover_conta(admin, jogador.id)
    assert repos.usuarios.buscar_por_id(jogador.id) is None
    assert repos.carteiras.buscar_por_id(jogador.id) is None


def test_crud_de_pacotes(adm_srv, admin, ofertas):
    p = adm_srv.criar_pacote(admin, "Teste", 100, limite_por_conta=2)
    assert p.id in {x.id for x in adm_srv.listar_pacotes(admin)}
    adm_srv.alterar_pacote(admin, p.id, tokens=250, ativo=False)
    alterado = [x for x in adm_srv.listar_pacotes(admin) if x.id == p.id][0]
    assert alterado.tokens == 250 and not alterado.ativo and alterado.limite_por_conta == 2
    assert adm_srv.remover_pacote(admin, p.id) is True
    with pytest.raises(DadosInvalidosException):
        adm_srv.alterar_pacote(admin, p.id, tokens=1)


def test_tudo_persiste_apos_reabrir(adm_srv, admin, jogador, tokens, tmp_path):
    adm_srv.definir_cota_diaria(admin, jogador.id, 12_345)
    tokens.registrar_consumo(jogador, "caso-1", "augusto", "gemini", 10, 10)
    novos = criar_repositorios(tmp_path)
    assert novos.carteiras.buscar_por_id(jogador.id).cota_diaria == 12_345
    assert len(novos.consumos.listar()) == 1
    assert novos.usuarios.buscar_por_id(admin.id).perfil == "administrador"
