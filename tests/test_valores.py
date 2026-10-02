import numpy as np
import pandas as pd

from gerador.valores import gerar_valores


def _ideias(n=6000):
    return pd.DataFrame({"id_ideia": range(1, n + 1),
                         "id_unidade": np.tile([1, 2, 3, 4, 5, 6], n // 6),
                         "id_etapa_atual": np.repeat([1, 2, 4, 6, 8, 7], n // 6),
                         "data_aprovacao": [None] * n})


def test_valores_por_etapa():
    v = gerar_valores(np.random.default_rng(1), _ideias())
    assert (v.ganho_previsto_12m.dropna() <= 990_000).all()
    assert (v.ganho_previsto_12m.dropna() > 0).all()
    assert v.loc[v.investimento_real.notna(), "id_etapa_atual"].isin([4, 5, 6]).all()
    taxa_inicio = v[v.id_etapa_atual == 1].ganho_previsto_12m.notna().mean()
    taxa_impl = v[v.id_etapa_atual == 6].ganho_previsto_12m.notna().mean()
    assert taxa_impl > taxa_inicio


def test_empresas_tem_proporcoes_diferentes():
    v = gerar_valores(np.random.default_rng(2), _ideias())
    s = v.groupby("id_unidade")[["ganho_previsto_12m", "investimento_previsto"]].sum()
    retorno = s.ganho_previsto_12m / s.investimento_previsto
    assert retorno.max() / retorno.min() > 1.5
