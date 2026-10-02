from datetime import date

import pandas as pd

from gerador.blocklist import bloqueado
from gerador.catalogos import ETAPAS, FAIXAS_DIAS, FAIXAS_VALOR, ORIGENS, TIPOS_GANHO, faixa_dias, faixa_valor


def validar(t: dict[str, pd.DataFrame], hoje: date, bloqueio: frozenset[str]) -> list[str]:
    e: list[str] = []
    pes, ide, mov = t["dim_pessoa"], t["fato_ideia"], t["fato_movimentacao"]

    if not pes.nome.is_unique:
        e.append("dim_pessoa: nome duplicado")
    if not ide.titulo.is_unique:
        e.append("fato_ideia: titulo duplicado")
    if any(bloqueado(n, bloqueio) for n in pes.nome):
        e.append("dim_pessoa: nome bloqueado (coincide com pessoa real)")
    if any(bloqueado(x, bloqueio) for x in ide.titulo):
        e.append("fato_ideia: titulo bloqueado (coincide com título real)")

    if (mov.data_entrada > hoje).any():
        e.append("fato_movimentacao: data_entrada futura")
    if (mov.data_saida.dropna() > hoje).any():
        e.append("fato_movimentacao: data_saida futura")
    if (ide.data_criacao > hoje).any():
        e.append("fato_ideia: data_criacao futura")

    abertas = mov.data_saida.isna().groupby(mov.id_ideia).sum()
    if not (abertas == 1).all():
        e.append("fato_movimentacao: ideia sem exatamente 1 etapa aberta")
    ordenado = mov.sort_values(["id_ideia", "seq"])
    prox = ordenado.groupby("id_ideia").data_entrada.shift(-1)
    fechadas = ordenado.data_saida.notna()
    if not (ordenado.data_saida[fechadas] == prox[fechadas]).all():
        e.append("fato_movimentacao: cadeia de datas quebrada")
    if not (ordenado.data_saida[fechadas] > ordenado.data_entrada[fechadas]).all():
        e.append("fato_movimentacao: saída não posterior à entrada")
    por_ideia = ide.set_index("id_ideia").sort_index()
    primeira = ordenado.groupby("id_ideia").data_entrada.first().sort_index()
    if not (por_ideia.data_criacao == primeira).all():
        e.append("fato_ideia: data_criacao difere da primeira movimentação")
    ultima = ordenado.groupby("id_ideia").id_etapa.last().sort_index()
    if not (por_ideia.id_etapa_atual == ultima).all():
        e.append("fato_ideia: id_etapa_atual difere da última movimentação")

    if not ide.id_autor.isin(pes.id_pessoa).all():
        e.append("fato_ideia: id_autor inexistente")
    if not ide.id_campanha.isin(t["dim_campanha"].id_campanha).all():
        e.append("fato_ideia: id_campanha inexistente")
    if not t["ponte_ideia_coautor"].id_pessoa.isin(pes.id_pessoa).all():
        e.append("ponte_ideia_coautor: pessoa inexistente")

    faltando = {x.id for x in ETAPAS} - set(mov.id_etapa)
    if faltando:
        e.append(f"etapas sem registro: {sorted(faltando)}")
    dias = [((s if s is not None and s == s else hoje) - en).days
            for en, s in zip(mov.data_entrada, mov.data_saida, strict=True)]
    if set(FAIXAS_DIAS) - {faixa_dias(d) for d in dias}:
        e.append("faixa de dias sem registro")
    if set(FAIXAS_VALOR) - {faixa_valor(g) for g in ide.ganho_previsto_12m}:
        e.append("faixa de valor sem registro")
    if set(range(1, len(ORIGENS) + 1)) - set(ide.id_origem.dropna().astype(int)):
        e.append("origem sem registro")
    if set(range(1, len(TIPOS_GANHO) + 1)) - set(t["ponte_ideia_ganho"].id_tipo_ganho):
        e.append("tipo de ganho sem registro")
    if set(t["dim_unidade"].id_unidade) - set(ide.id_unidade):
        e.append("unidade sem ideias")
    return e
