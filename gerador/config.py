from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

TRANSICOES_BASE: dict[int, dict[int, float]] = {
    1: {2: .66, 8: .13, 7: .12, 3: .06, 9: .03},
    2: {3: .64, 8: .13, 1: .10, 7: .09, 9: .04},
    3: {4: .88, 2: .05, 8: .04, 9: .03},
    4: {5: .83, 3: .05, 2: .03, 1: .02, 8: .03, 9: .04},
    5: {6: .85, 4: .12, 8: .03},
    7: {1: .55, 8: .30, 9: .15},
    8: {2: .50, 4: .50},
}
MEDIANA_DIAS_BASE = {1: 12, 2: 35, 3: 30, 4: 60, 5: 15, 7: 90, 8: 30}


@dataclass(frozen=True)
class Parametros:
    semente: int
    hoje: date
    data_inicio: date
    funcionarios_por_unidade: tuple[int, ...]
    n_ideias: int
    participacao: float
    transicoes: dict
    mediana_dias: dict
    sigma: float
    prob_reabrir: float

    def __hash__(self) -> int:
        return hash((self.semente, self.hoje))


def sortear_parametros(semente: int, hoje: date) -> Parametros:
    rng = np.random.default_rng(semente)
    meses = int(rng.integers(24, 37))
    transicoes = {}
    for origem, destinos in TRANSICOES_BASE.items():
        pesos = {d: w * float(rng.uniform(0.7, 1.3)) for d, w in destinos.items()}
        total = sum(pesos.values())
        transicoes[origem] = {d: w / total for d, w in pesos.items()}
    return Parametros(
        semente=semente,
        hoje=hoje,
        data_inicio=hoje - timedelta(days=round(meses * 30.44)),
        funcionarios_por_unidade=tuple(int(x) for x in rng.integers(50, 501, size=6)),
        n_ideias=int(rng.integers(700, 1501)),
        participacao=float(rng.uniform(0.15, 0.40)),
        transicoes=transicoes,
        mediana_dias={k: v * float(rng.uniform(0.75, 1.25)) for k, v in MEDIANA_DIAS_BASE.items()},
        sigma=float(rng.uniform(0.7, 1.0)),
        prob_reabrir=float(rng.uniform(0.01, 0.04)),
    )
