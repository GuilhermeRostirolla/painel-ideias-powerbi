from datetime import date

import numpy as np

from gerador.blocklist import hash_texto
from gerador.catalogos import gerar_empresas
from gerador.config import sortear_parametros
from gerador.pessoas import gerar_campanhas, gerar_pessoas, gerar_unidades


def _base():
    p = sortear_parametros(7, date(2026, 9, 30))
    return p, gerar_unidades(p, gerar_empresas(np.random.default_rng(7), frozenset()))


def test_unidades():
    p, u = _base()
    assert u.sigla.is_unique and u.nome.is_unique and len(u) == 6
    assert list(u.qtd_funcionarios) == list(p.funcionarios_por_unidade)


def test_pessoas_unicas_quantidade_e_gestores():
    p, u = _base()
    pes = gerar_pessoas(np.random.default_rng(7), u, frozenset())
    assert len(pes) == sum(p.funcionarios_por_unidade)
    assert pes.nome.is_unique
    assert pes.groupby("id_unidade").size().tolist() == list(p.funcionarios_por_unidade)
    gest = pes[pes.eh_gestor]
    assert gest.id_gestor.isna().all()
    comuns = pes[~pes.eh_gestor]
    assert comuns.id_gestor.isin(gest.id_pessoa).all()
    mesma = comuns.merge(gest[["id_pessoa", "id_unidade"]], left_on="id_gestor", right_on="id_pessoa")
    assert (mesma.id_unidade_x == mesma.id_unidade_y).all()
    assert pes.eh_gestor.iloc[: len(gest)].all()


def test_pessoas_respeitam_bloqueio():
    _, u = _base()
    livre = gerar_pessoas(np.random.default_rng(7), u, frozenset())
    bl = frozenset(hash_texto(n) for n in livre.nome.iloc[:20])
    pes = gerar_pessoas(np.random.default_rng(7), u, bl)
    assert not set(livre.nome.iloc[:20]) & set(pes.nome)


def test_campanhas_duas_por_unidade():
    p, u = _base()
    c = gerar_campanhas(u, p.data_inicio)
    assert len(c) == 12 and c.id_campanha.is_unique
    assert set(c.id_tipo) == {1, 2}
    assert (c.data_inicio == p.data_inicio).all()
