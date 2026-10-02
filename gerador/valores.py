from math import log

import numpy as np
import pandas as pd

_ETAPAS_COM_GASTO = (4, 5, 6)


def _perfil_empresas(rng: np.random.Generator, unidades: np.ndarray) -> dict[int, tuple[float, float]]:
    return {int(u): (float(rng.uniform(1.5, 5.0)), float(rng.uniform(0.5, 1.4))) for u in unidades}


def gerar_valores(rng: np.random.Generator, ideias: pd.DataFrame) -> pd.DataFrame:
    v = ideias.copy()
    n = len(v)
    perfil = _perfil_empresas(rng, np.unique(v.id_unidade))
    retorno = np.array([perfil[int(u)][0] for u in v.id_unidade])
    execucao = np.array([perfil[int(u)][1] for u in v.id_unidade])

    avancou = (v.id_etapa_atual.isin([2, 3, 4, 5, 6]) | v.data_aprovacao.notna()).to_numpy()
    tem_valor = rng.random(n) < np.where(avancou, 0.70, 0.15)
    ganho = np.minimum(990_000, np.round(rng.lognormal(log(40_000), 1.2, size=n), -2))
    ganho = np.maximum(ganho, 100)
    previsto = np.maximum(100, np.round(ganho / (retorno * rng.lognormal(0, 0.35, size=n)), -2))
    real = np.round(np.minimum(previsto * 1.3, previsto * execucao * rng.uniform(0.8, 1.25, size=n)), -2)
    v["ganho_previsto_12m"] = np.where(tem_valor, ganho, np.nan)
    v["investimento_previsto"] = np.where(tem_valor, previsto, np.nan)
    gasto = tem_valor & v.id_etapa_atual.isin(_ETAPAS_COM_GASTO).to_numpy()
    v["investimento_real"] = np.where(gasto, real, np.nan)
    return v
