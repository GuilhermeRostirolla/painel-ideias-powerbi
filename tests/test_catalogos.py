from datetime import date

import numpy as np

from gerador import catalogos as cat
from gerador.blocklist import hash_texto
from gerador.config import sortear_parametros


def test_etapas_ids_1_a_9_na_ordem_do_dax():
    assert [e.id for e in cat.ETAPAS] == list(range(1, 10))
    assert cat.ETAPAS[0].estado == "ETAPA 1: AVALIAÇÃO"
    assert {e.id for e in cat.ETAPAS if e.terminal} == {6, 8, 9}


def test_catalogos_tamanhos():
    assert len(cat.ORIGENS) == 13 and len(cat.TIPOS_GANHO) == 15
    assert cat.TIPOS_GANHO[0] == "Em Etapas Anteriores"
    assert len(set(cat.TEMAS)) == len(cat.TEMAS) == 5


def test_faixa_valor():
    assert cat.faixa_valor(None) == "0-Sem valor"
    assert cat.faixa_valor(0) == "0-Sem valor"
    assert cat.faixa_valor(50_000) == "1-Até 50K"
    assert cat.faixa_valor(50_001) == "2-50K até 100K"
    assert cat.faixa_valor(400_000) == "3-100K até 500K"
    assert cat.faixa_valor(900_000) == "4-500K até 1M"


def test_faixa_dias_igual_ao_dax():
    assert [cat.faixa_dias(d) for d in (0, 15, 16, 30, 31, 60, 61)] == [
        "0–15 d", "0–15 d", "16–30 d", "16–30 d", "31–60 d", "31–60 d", "+60 d"]


def test_titulos_unicos_e_respeitam_bloqueio():
    livres = cat.gerar_titulos(np.random.default_rng(1), 50, frozenset())
    bloqueio = frozenset({hash_texto(livres[0])})
    t = cat.gerar_titulos(np.random.default_rng(1), 1500, bloqueio)
    assert len(t) == 1500 == len(set(t))
    assert livres[0] not in t


def test_titulos_com_contracao():
    t = cat.gerar_titulos(np.random.default_rng(2), 2000, frozenset())
    assert not any(x in titulo for titulo in t for x in (" de a ", " de o ", " em a ", " em o "))
    assert any(titulo.startswith("Reduzir o tempo da ") for titulo in t)


def test_sortear_parametros_faixas():
    p = sortear_parametros(123, date(2026, 9, 30))
    assert p.hoje == date(2026, 9, 30)
    meses = (p.hoje - p.data_inicio).days / 30.44
    assert 23.5 <= meses <= 36.5
    assert len(p.funcionarios_por_unidade) == 6
    assert all(50 <= f <= 500 for f in p.funcionarios_por_unidade)
    assert 700 <= p.n_ideias <= 1500 and 0.15 <= p.participacao <= 0.40
    for destinos in p.transicoes.values():
        assert abs(sum(destinos.values()) - 1) < 1e-9
    assert sortear_parametros(123, p.hoje) == p


def test_gerar_empresas_unicas_e_bloqueio():
    e = cat.gerar_empresas(np.random.default_rng(3), frozenset())
    assert len(e) == 6 and len({n for n, _ in e}) == 6 and len({s for _, s in e}) == 6
    assert all(n.startswith(s) and len(s) <= 20 for n, s in e)
    bl = frozenset({hash_texto(e[0][0].split()[0])})
    e2 = cat.gerar_empresas(np.random.default_rng(3), bl)
    assert e[0][0] not in {n for n, _ in e2}
    outra = cat.gerar_empresas(np.random.default_rng(4), frozenset())
    assert outra != e


def test_titulos_coerentes_e_rotulos_curtos():
    t = cat.gerar_titulos(np.random.default_rng(5), 1500, frozenset())
    assert not any("paletes no escritório" in x or "instrumentos no RH" in x for x in t)
    assert all(len(g) <= 17 for g in cat.TIPOS_GANHO[1:])
