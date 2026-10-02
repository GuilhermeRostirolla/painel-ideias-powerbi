from datetime import date, timedelta
from math import log

import numpy as np
import pandas as pd

from gerador.config import Parametros

_TERMINAIS_FIXOS = (6, 9)
_MAX_PASSOS = 40
_MAX_DIAS_ETAPA = 365


def _duracao(rng: np.random.Generator, mediana: float, sigma: float) -> int:
    return min(_MAX_DIAS_ETAPA, max(1, round(float(rng.lognormal(log(mediana), sigma)))))


def _proxima(rng: np.random.Generator, destinos: dict[int, float]) -> int:
    ids = list(destinos)
    return int(rng.choice(ids, p=[destinos[i] for i in ids]))


def simular_ideia(rng: np.random.Generator, criacao: date,
                  p: Parametros) -> list[tuple[int, date, date | None]]:
    etapa = 7 if rng.random() < 0.10 else 1
    entrada = criacao
    movs: list[tuple[int, date, date | None]] = []
    for _ in range(_MAX_PASSOS):
        encerra = etapa in _TERMINAIS_FIXOS or (etapa == 8 and rng.random() >= p.prob_reabrir)
        if encerra:
            break
        saida = entrada + timedelta(days=_duracao(rng, p.mediana_dias[etapa], p.sigma))
        if saida > p.hoje:
            break
        movs.append((etapa, entrada, saida))
        etapa = _proxima(rng, p.transicoes[etapa])
        entrada = saida
    movs.append((etapa, entrada, None))
    return movs


def simular_todas(rng: np.random.Generator, ideias: pd.DataFrame, p: Parametros) -> pd.DataFrame:
    linhas = []
    for id_ideia, criacao in zip(ideias.id_ideia, ideias.data_criacao, strict=True):
        for seq, (etapa, entrada, saida) in enumerate(simular_ideia(rng, criacao, p), start=1):
            linhas.append((int(id_ideia), seq, etapa, entrada, saida))
    return pd.DataFrame(linhas, columns=["id_ideia", "seq", "id_etapa", "data_entrada", "data_saida"])
