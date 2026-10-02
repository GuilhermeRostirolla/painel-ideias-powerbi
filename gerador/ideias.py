from datetime import date, timedelta

import numpy as np
import pandas as pd

from gerador.catalogos import MOTIVOS_REPROVACAO, ORIGENS, TEMAS, TIPOS_GANHO, gerar_descricao
from gerador.config import Parametros


def _datas_criacao(rng: np.random.Generator, p: Parametros, n: int) -> list[date]:
    dias = pd.bdate_range(p.data_inicio, p.hoje - timedelta(days=1))
    t = np.linspace(0, 1, len(dias))
    peso = 0.6 + 0.8 * t
    idx = np.sort(rng.choice(len(dias), size=n, p=peso / peso.sum()))
    return [dias[i].date() for i in idx]


def gerar_ideias(rng: np.random.Generator, p: Parametros, pessoas: pd.DataFrame,
                 campanhas: pd.DataFrame, titulos: list[str]) -> pd.DataFrame:
    n = p.n_ideias
    por_unidade = pessoas.groupby("id_unidade").id_pessoa.apply(lambda s: s.to_numpy())
    unidades = por_unidade.index.to_numpy()
    peso_u = np.array([len(ids) for ids in por_unidade]) * rng.uniform(0.7, 1.3, size=len(unidades))
    id_unidade = rng.choice(unidades, size=n, p=peso_u / peso_u.sum())
    id_autor = np.empty(n, dtype=int)
    for u, ids in por_unidade.items():
        autores = rng.choice(ids, size=min(len(ids), max(5, round(len(ids) * p.participacao))),
                             replace=False)
        peso = rng.lognormal(0.0, 1.1, size=len(autores))
        alvo = id_unidade == u
        id_autor[alvo] = rng.choice(autores, size=int(alvo.sum()), p=peso / peso.sum())
    camp = {(r.id_unidade, r.id_tipo): r.id_campanha for r in campanhas.itertuples()}
    tipo = np.where(rng.random(n) < 0.7, 1, 2)
    origem = pd.array(rng.integers(1, len(ORIGENS) + 1, size=n), dtype="Int64")
    origem[rng.random(n) < 0.05] = pd.NA
    return pd.DataFrame({
        "id_ideia": np.arange(1, n + 1),
        "titulo": titulos[:n],
        "descricao": [gerar_descricao(rng, t) for t in titulos[:n]],
        "id_autor": id_autor.astype(int),
        "id_unidade": id_unidade.astype(int),
        "id_campanha": [camp[(u, t)] for u, t in zip(id_unidade, tipo, strict=True)],
        "id_tema": rng.integers(1, len(TEMAS) + 1, size=n),
        "id_origem": origem,
        "data_criacao": _datas_criacao(rng, p, n),
    })


def _primeira(movs: pd.DataFrame, etapa: int) -> pd.Series:
    return movs[movs.id_etapa == etapa].groupby("id_ideia").data_entrada.min()


def derivar_campos(rng: np.random.Generator, ideias: pd.DataFrame, movs: pd.DataFrame,
                   pessoas: pd.DataFrame) -> pd.DataFrame:
    ult = movs.sort_values(["id_ideia", "seq"]).groupby("id_ideia").tail(1).set_index("id_ideia")
    d = ideias.set_index("id_ideia").copy()
    d["id_etapa_atual"] = ult.id_etapa
    d["data_ultima_mov"] = ult.data_entrada
    d["data_aprovacao"] = _primeira(movs, 3)
    d["data_inicio_impl"] = _primeira(movs, 4)
    d["data_implantacao"] = movs[movs.id_etapa == 6].groupby("id_ideia").data_entrada.max()
    rep = d.id_etapa_atual == 8
    d["data_reprovacao"] = d.data_ultima_mov.where(rep)
    motivo = pd.Series(rng.integers(1, len(MOTIVOS_REPROVACAO) + 1, size=len(d)), index=d.index)
    d["id_motivo_reprovacao"] = motivo.where(rep).astype("Int64")
    por_unidade = pessoas.groupby("id_unidade").id_pessoa.apply(lambda s: s.to_numpy())
    resp, ini, fim = [], [], []
    for u, apr in zip(d.id_unidade, d.data_aprovacao, strict=True):
        if pd.isna(apr):
            resp.append(pd.NA)
            ini.append(None)
            fim.append(None)
            continue
        resp.append(int(rng.choice(por_unidade[u])))
        i = apr + timedelta(days=int(rng.integers(5, 21)))
        ini.append(i)
        fim.append(i + timedelta(days=int(rng.integers(30, 151))))
    d["id_responsavel_impl"] = pd.array(resp, dtype="Int64")
    d["data_inicio_previsto"] = pd.Series(ini, index=d.index, dtype=object)
    d["data_termino_previsto"] = pd.Series(fim, index=d.index, dtype=object)
    for col in ("data_aprovacao", "data_inicio_impl", "data_implantacao", "data_reprovacao"):
        d[col] = d[col].astype(object).where(d[col].notna(), None)
    return d.reset_index()


def gerar_coautores(rng: np.random.Generator, ideias: pd.DataFrame,
                    pessoas: pd.DataFrame) -> pd.DataFrame:
    por_unidade = pessoas.groupby("id_unidade").id_pessoa.apply(lambda s: s.to_numpy())
    linhas = []
    for r in ideias.itertuples():
        k = int(rng.choice([0, 1, 2, 3], p=[.5, .3, .15, .05]))
        candidatos = por_unidade[r.id_unidade]
        candidatos = candidatos[candidatos != r.id_autor]
        for pid in rng.choice(candidatos, size=min(k, len(candidatos)), replace=False):
            linhas.append((int(r.id_ideia), int(pid)))
    return pd.DataFrame(linhas, columns=["id_ideia", "id_pessoa"])


def gerar_ganhos(rng: np.random.Generator, ideias: pd.DataFrame,
                 movs: pd.DataFrame) -> pd.DataFrame:
    avancou = set(movs[movs.id_etapa.isin([2, 3, 4, 5, 6])].id_ideia)
    linhas = []
    for id_ideia in ideias.id_ideia:
        if id_ideia in avancou:
            k = int(rng.choice([1, 2, 3], p=[.5, .35, .15]))
            tipos = rng.choice(np.arange(2, len(TIPOS_GANHO) + 1), size=k, replace=False)
        else:
            tipos = [1]
        linhas.extend((int(id_ideia), int(t)) for t in tipos)
    return pd.DataFrame(linhas, columns=["id_ideia", "id_tipo_ganho"])
