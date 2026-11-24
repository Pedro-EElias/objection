"""Conversão entre objetos de domínio e dicionários JSON."""
from datetime import date, datetime

from objection.dominio.enums import (
    FaixaConfianca, FasePartida, NivelJogador, Permissao, ResultadoVeredito, StatusConta,
)
from objection.dominio.partida import Partida
from objection.dominio.resultado import HistoricoEvento, Veredito
from objection.dominio.tokens import CarteiraTokens, PacoteTokens, RegistroConsumo, ResgateOferta
from objection.dominio.usuario import Administrador, Jogador, Usuario
from objection.excecoes import DadosCorrompidosException


def _data(valor):
    return date.fromisoformat(valor) if valor else None


def usuario_para_dict(u: Usuario) -> dict:
    base = {"id": u.id, "apelido": u.apelido, "senha_hash": u.senha_hash, "salt": u.salt,
            "iteracoes": u.iteracoes, "status": u.status.value}
    if isinstance(u, Jogador):
        base.update(tipo="jogador", nivel=u.nivel.value,
                    partidas_concluidas=sorted(u.partidas_concluidas), vitorias=u.vitorias)
    elif isinstance(u, Administrador):
        base.update(tipo="administrador", permissoes=sorted(p.value for p in u.permissoes))
    else:
        raise DadosCorrompidosException(f"Tipo de usuário desconhecido: {type(u).__name__}")
    return base


def usuario_de_dict(d: dict) -> Usuario:
    try:
        comum = (d["id"], d["apelido"], d["senha_hash"], d["salt"], d["iteracoes"])
        status = StatusConta(d["status"])
        if d["tipo"] == "jogador":
            return Jogador(*comum, status=status, nivel=NivelJogador(d["nivel"]),
                           partidas_concluidas=d["partidas_concluidas"], vitorias=d["vitorias"])
        if d["tipo"] == "administrador":
            return Administrador(*comum, status=status,
                                 permissoes={Permissao(p) for p in d["permissoes"]})
    except (KeyError, ValueError, TypeError) as erro:
        raise DadosCorrompidosException(f"Registro de usuário inválido: {erro}") from None
    raise DadosCorrompidosException(f"Tipo de usuário desconhecido: {d.get('tipo')}")


def carteira_para_dict(c: CarteiraTokens) -> dict:
    return {"id_conta": c.id_conta, "cota_diaria": c.cota_diaria, "cota_por_caso": c.cota_por_caso,
            "saldo": c.saldo, "data_recarga": c.data_recarga.isoformat() if c.data_recarga else None,
            "consumo_por_caso": c.consumo_por_caso}


def carteira_de_dict(d: dict) -> CarteiraTokens:
    try:
        return CarteiraTokens(d["id_conta"], d["cota_diaria"], d["cota_por_caso"], d["saldo"],
                              _data(d["data_recarga"]), d["consumo_por_caso"])
    except (KeyError, ValueError, TypeError) as erro:
        raise DadosCorrompidosException(f"Registro de carteira inválido: {erro}") from None


def consumo_para_dict(r: RegistroConsumo) -> dict:
    return {"id": r.id, "id_conta": r.id_conta, "id_caso": r.id_caso, "id_juiz": r.id_juiz,
            "provedor": r.provedor, "tokens_entrada": r.tokens_entrada,
            "tokens_saida": r.tokens_saida, "simulado": r.simulado,
            "momento": r.momento.isoformat()}


def consumo_de_dict(d: dict) -> RegistroConsumo:
    try:
        return RegistroConsumo(d["id"], d["id_conta"], d["id_caso"], d["id_juiz"], d["provedor"],
                               d["tokens_entrada"], d["tokens_saida"], d["simulado"],
                               datetime.fromisoformat(d["momento"]))
    except (KeyError, ValueError, TypeError) as erro:
        raise DadosCorrompidosException(f"Registro de consumo inválido: {erro}") from None


def pacote_para_dict(p: PacoteTokens) -> dict:
    return {"id": p.id, "nome": p.nome, "tokens": p.tokens, "limite_por_conta": p.limite_por_conta,
            "uma_por_dia": p.uma_por_dia,
            "validade_ate": p.validade_ate.isoformat() if p.validade_ate else None,
            "ativo": p.ativo}


def pacote_de_dict(d: dict) -> PacoteTokens:
    try:
        return PacoteTokens(d["id"], d["nome"], d["tokens"], d["limite_por_conta"],
                            d["uma_por_dia"], _data(d["validade_ate"]), d["ativo"])
    except (KeyError, ValueError, TypeError) as erro:
        raise DadosCorrompidosException(f"Registro de pacote inválido: {erro}") from None


def resgate_para_dict(r: ResgateOferta) -> dict:
    return {"id": r.id, "id_conta": r.id_conta, "id_pacote": r.id_pacote,
            "data": r.data.isoformat(), "tokens": r.tokens}


def resgate_de_dict(d: dict) -> ResgateOferta:
    try:
        return ResgateOferta(d["id"], d["id_conta"], d["id_pacote"], date.fromisoformat(d["data"]),
                             d["tokens"])
    except (KeyError, ValueError, TypeError) as erro:
        raise DadosCorrompidosException(f"Registro de resgate inválido: {erro}") from None


def _evento_para_dict(e: HistoricoEvento) -> dict:
    return {"rodada": e.rodada, "id_acao": e.id_acao, "descricao": e.descricao, "sucesso": e.sucesso,
            "delta_confianca": e.delta_confianca, "delta_suspeita": e.delta_suspeita,
            "motivos": list(e.motivos)}


def _evento_de_dict(d: dict) -> HistoricoEvento:
    return HistoricoEvento(d["rodada"], d["id_acao"], d["descricao"], d["sucesso"],
                           d["delta_confianca"], d["delta_suspeita"], tuple(d["motivos"]))


def partida_para_dict(p: Partida) -> dict:
    v = p.veredito
    return {
        "id": p.id, "id_caso": p.id_caso, "id_jogador": p.id_jogador, "id_juiz": p.id_juiz,
        "nome": p.nome, "fase": p.fase.value, "orcamento": p.orcamento,
        "confianca": p.confianca, "suspeita": p.suspeita,
        "evidencias": sorted(p.evidencias_descobertas), "testemunhas": sorted(p.testemunhas_preparadas),
        "alibi": p.alibi_preparado, "suborno": p.suborno_tentado,
        "acoes": sorted(p.acoes_executadas), "afirmacoes": list(p.afirmacoes), "rodada": p.rodada,
        "historico": [_evento_para_dict(e) for e in p.historico], "versao": p.versao,
        "veredito": None if v is None else {
            "resultado": v.resultado.value, "confianca_final": v.confianca_final,
            "suspeita_final": v.suspeita_final, "faixa": v.faixa.value, "motivos": list(v.motivos)},
    }


def partida_de_dict(d: dict) -> Partida:
    try:
        v = d["veredito"]
        veredito = None if v is None else Veredito(
            ResultadoVeredito(v["resultado"]), v["confianca_final"], v["suspeita_final"],
            FaixaConfianca(v["faixa"]), tuple(v["motivos"]))
        return Partida.restaurar(
            d["id"], d["id_caso"], d["id_jogador"], d["id_juiz"], d["nome"], FasePartida(d["fase"]),
            d["orcamento"], d["confianca"], d["suspeita"], d["evidencias"], d["testemunhas"],
            d["alibi"], d["suborno"], d["acoes"], d["afirmacoes"], d["rodada"],
            [_evento_de_dict(e) for e in d["historico"]], veredito, d["versao"])
    except (KeyError, ValueError, TypeError) as erro:
        raise DadosCorrompidosException(f"Registro de partida inválido: {erro}") from None
