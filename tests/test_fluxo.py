from datetime import date, timedelta

import numpy as np
import pandas as pd

from gerador.config import sortear_parametros
from gerador.fluxo import simular_ideia, simular_todas

HOJE = date(2026, 9, 30)


def test_cadeia_coerente_muitas_sementes():
    p = sortear_parametros(3, HOJE)
    rng = np.random.default_rng(3)
    for k in range(2000):
        criacao = p.data_inicio + timedelta(days=k % 700)
        movs = simular_ideia(rng, criacao, p)
        assert movs[0][1] == criacao
        assert movs[0][0] in (1, 7)
        assert movs[-1][2] is None
        assert all(m[2] is not None for m in movs[:-1])
        for a, b in zip(movs, movs[1:], strict=False):
            assert a[2] == b[1] and a[2] > a[1]
        assert all(m[1] <= HOJE for m in movs)


def test_terminais_encerram():
    p = sortear_parametros(4, HOJE)
    rng = np.random.default_rng(4)
    for _ in range(500):
        movs = simular_ideia(rng, p.data_inicio, p)
        for m in movs[:-1]:
            assert m[0] not in (6, 9)


def test_simular_todas_formato():
    p = sortear_parametros(5, HOJE)
    ideias = pd.DataFrame({"id_ideia": [1, 2, 3],
                           "data_criacao": [p.data_inicio, date(2026, 1, 5), date(2026, 9, 29)]})
    m = simular_todas(np.random.default_rng(5), ideias, p)
    assert list(m.columns) == ["id_ideia", "seq", "id_etapa", "data_entrada", "data_saida"]
    assert m.groupby("id_ideia").data_saida.apply(lambda s: s.isna().sum()).eq(1).all()
    assert m.groupby("id_ideia").seq.apply(lambda s: list(s) == list(range(1, len(s) + 1))).all()


def test_nenhuma_etapa_passa_de_um_ano():
    p = sortear_parametros(6, HOJE)
    rng = np.random.default_rng(6)
    for k in range(3000):
        for etapa, entrada, saida in simular_ideia(rng, p.data_inicio + timedelta(days=k % 300), p):
            if etapa not in (6, 8, 9):
                assert ((saida or HOJE) - entrada).days <= 365
