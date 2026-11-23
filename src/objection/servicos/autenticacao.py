import uuid
from datetime import datetime

from objection.config import CONFIG_PADRAO
from objection.dominio.enums import StatusConta
from objection.dominio.tokens import CarteiraTokens
from objection.dominio.usuario import Administrador, Jogador
from objection.excecoes import ApelidoEmUsoException, CredenciaisInvalidasException


class ServicoAutenticacao:
    """Cadastro, login e manutenção da própria conta (CRUD da conta)."""

    def __init__(self, repos, config=CONFIG_PADRAO, relogio=datetime.now):
        self._repos = repos
        self._config = config
        self._relogio = relogio

    def _apelido_em_uso(self, apelido, ignorar_id=None) -> bool:
        alvo = apelido.strip().lower()
        return any(u.apelido.lower() == alvo and u.id != ignorar_id
                   for u in self._repos.usuarios.listar())

    def cadastrar_jogador(self, apelido, senha) -> Jogador:
        if self._apelido_em_uso(apelido):
            raise ApelidoEmUsoException(f"O apelido '{apelido}' já está em uso.")
        jogador = Jogador.novo(uuid.uuid4().hex[:12], apelido, senha)
        self._repos.usuarios.salvar(jogador)
        self._repos.carteiras.salvar(CarteiraTokens(
            jogador.id, self._config.cota_diaria_padrao, self._config.cota_por_caso_padrao))
        return jogador

    def cadastrar_administrador(self, apelido, senha) -> Administrador:
        if self._apelido_em_uso(apelido):
            raise ApelidoEmUsoException(f"O apelido '{apelido}' já está em uso.")
        admin = Administrador.novo(uuid.uuid4().hex[:12], apelido, senha)
        self._repos.usuarios.salvar(admin)
        return admin

    def login(self, apelido, senha):
        alvo = str(apelido).strip().lower()
        for u in self._repos.usuarios.listar():
            if u.apelido.lower() == alvo and u.status is not StatusConta.EXCLUIDA:
                if u.verificar_senha(senha):
                    return u
                break
        raise CredenciaisInvalidasException("Usuário ou senha incorretos.")

    def consultar(self, id_usuario):
        return self._repos.usuarios.buscar_por_id(id_usuario)

    def alterar_apelido(self, usuario, novo_apelido):
        if self._apelido_em_uso(novo_apelido, ignorar_id=usuario.id):
            raise ApelidoEmUsoException(f"O apelido '{novo_apelido}' já está em uso.")
        usuario.definir_apelido(novo_apelido)
        self._repos.usuarios.salvar(usuario)

    def alterar_senha(self, usuario, senha_atual, nova_senha):
        if not usuario.verificar_senha(senha_atual):
            raise CredenciaisInvalidasException("A senha atual está incorreta.")
        usuario.definir_senha(nova_senha)
        self._repos.usuarios.salvar(usuario)

    def excluir_conta(self, usuario, senha):
        """Remove a conta e a carteira. O livro de consumo é mantido para auditoria."""
        if not usuario.verificar_senha(senha):
            raise CredenciaisInvalidasException("Senha incorreta.")
        usuario.marcar_excluida()
        self._repos.usuarios.remover(usuario.id)
        self._repos.carteiras.remover(usuario.id)
