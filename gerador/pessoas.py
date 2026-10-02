from datetime import date

import numpy as np
import pandas as pd
from faker import Faker

from gerador.blocklist import bloqueado
from gerador.catalogos import TIPOS_CAMPANHA
from gerador.config import Parametros


def gerar_unidades(p: Parametros, empresas: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame({
        "id_unidade": range(1, len(empresas) + 1),
        "nome": [e[0] for e in empresas],
        "sigla": [e[1] for e in empresas],
        "qtd_funcionarios": list(p.funcionarios_por_unidade[:len(empresas)]),
    })


def _nomes_unicos(rng: np.random.Generator, n: int, bloqueio: frozenset[str]) -> list[str]:
    fake = Faker("pt_BR")
    fake.seed_instance(int(rng.integers(2**31)))
    vistos: set[str] = set()
    nomes: list[str] = []
    while len(nomes) < n:
        nome = f"{fake.first_name()} {fake.last_name()}"
        if rng.random() < 0.5:
            nome += f" {fake.last_name()}"
        if nome in vistos or bloqueado(nome, bloqueio):
            continue
        vistos.add(nome)
        nomes.append(nome)
    return nomes


def gerar_pessoas(rng: np.random.Generator, unidades: pd.DataFrame,
                  bloqueio: frozenset[str]) -> pd.DataFrame:
    nomes = iter(_nomes_unicos(rng, int(unidades.qtd_funcionarios.sum()), bloqueio))
    gestores, comuns = [], []
    proximo_id = 1
    for u in unidades.itertuples():
        n_gest = max(1, u.qtd_funcionarios // 15)
        ids_gest = list(range(proximo_id, proximo_id + n_gest))
        for i in ids_gest:
            gestores.append((i, next(nomes), u.id_unidade, None, True))
        proximo_id += n_gest
        for _ in range(u.qtd_funcionarios - n_gest):
            chefe = int(rng.choice(ids_gest))
            comuns.append((proximo_id, next(nomes), u.id_unidade, chefe, False))
            proximo_id += 1
    df = pd.DataFrame(gestores + comuns,
                      columns=["id_pessoa", "nome", "id_unidade", "id_gestor", "eh_gestor"])
    df["id_gestor"] = df["id_gestor"].astype("Int64")
    return df


def gerar_campanhas(unidades: pd.DataFrame, data_inicio: date) -> pd.DataFrame:
    linhas = []
    for u in unidades.itertuples():
        for id_tipo, tipo, rotulo in TIPOS_CAMPANHA:
            linhas.append((len(linhas) + 1, f"{rotulo} {u.sigla}", tipo, id_tipo,
                           u.id_unidade, data_inicio))
    return pd.DataFrame(linhas, columns=["id_campanha", "nome", "tipo", "id_tipo",
                                         "id_unidade", "data_inicio"])
