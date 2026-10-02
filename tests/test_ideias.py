from datetime import date

import numpy as np

from gerador.catalogos import gerar_empresas, gerar_titulos
from gerador.config import sortear_parametros
from gerador.fluxo import simular_todas
from gerador.ideias import derivar_campos, gerar_coautores, gerar_ganhos, gerar_ideias
from gerador.pessoas import gerar_campanhas, gerar_pessoas, gerar_unidades

HOJE = date(2026, 9, 30)


def _cenario(semente=11):
    rng = np.random.default_rng(semente)
    p = sortear_parametros(semente, HOJE)
    u = gerar_unidades(p, gerar_empresas(rng, frozenset()))
    pes = gerar_pessoas(rng, u, frozenset())
    camp = gerar_campanhas(u, p.data_inicio)
    tit = gerar_titulos(rng, p.n_ideias, frozenset())
    ide = gerar_ideias(rng, p, pes, camp, tit)
    movs = simular_todas(rng, ide, p)
    return rng, p, pes, camp, ide, movs


def test_gerar_ideias():
    _, p, pes, camp, ide, _ = _cenario()
    assert len(ide) == p.n_ideias and ide.titulo.is_unique
    assert ide.data_criacao.between(p.data_inicio, HOJE).all()
    assert all(d.weekday() < 5 for d in ide.data_criacao)
    j = ide.merge(pes, left_on="id_autor", right_on="id_pessoa")
    assert (j.id_unidade_x == j.id_unidade_y).all()
    jc = ide.merge(camp, on="id_campanha")
    assert (jc.id_unidade_x == jc.id_unidade_y).all()
    autores = ide.id_autor.value_counts()
    assert autores.max() >= 10 and (autores == 1).any()
    assert autores.max() <= 0.06 * len(ide)
    por_empresa = ide.id_unidade.value_counts(normalize=True)
    assert len(por_empresa) == 6 and por_empresa.min() >= 0.03


def test_derivar_campos():
    rng, _, pes, _, ide, movs = _cenario()
    d = derivar_campos(rng, ide, movs, pes)
    ult = movs.sort_values("seq").groupby("id_ideia").tail(1).set_index("id_ideia").sort_index()
    assert (d.set_index("id_ideia").sort_index().id_etapa_atual == ult.id_etapa).all()
    rep = d[d.id_etapa_atual == 8]
    assert rep.id_motivo_reprovacao.notna().all() and rep.data_reprovacao.notna().all()
    assert d[d.id_etapa_atual != 8].id_motivo_reprovacao.isna().all()
    impl = d[d.id_etapa_atual == 6]
    assert impl.data_implantacao.notna().all()
    apr = d[d.data_aprovacao.notna()]
    assert apr.id_responsavel_impl.notna().all()
    assert (apr.data_termino_previsto > apr.data_inicio_previsto).all()


def test_coautores_e_ganhos():
    rng, _, pes, _, ide, movs = _cenario()
    co = gerar_coautores(rng, ide, pes)
    assert not co.duplicated().any()
    j = co.merge(ide[["id_ideia", "id_autor"]], on="id_ideia")
    assert (j.id_pessoa != j.id_autor).all()
    g = gerar_ganhos(rng, ide, movs)
    assert set(g.id_ideia) == set(ide.id_ideia)
    assert g.id_tipo_ganho.between(1, 15).all() and not g.duplicated().any()
