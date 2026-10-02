from datetime import date

import pytest
from sqlalchemy import text

from gerador import banco
from gerador.main import SQL, construir

BANCO = "IdeiasDemoTeste"


@pytest.mark.sql
def test_carga_completa_views_e_checks():
    tabelas = construir(99, date.today(), frozenset())
    banco.recriar_banco("localhost", BANCO)
    eng = banco.criar_engine("localhost", BANCO)
    try:
        banco.executar_script(eng, SQL / "01_schema.sql")
        banco.gravar(eng, tabelas)
        banco.executar_script(eng, SQL / "03_views_compat.sql")
        assert banco.rodar_checks(eng, SQL / "04_checks.sql") == []
        with eng.connect() as c:
            n = c.execute(text("SELECT COUNT(*) FROM bi.vw_Fato_Ideias")).scalar()
            cols = [r[0] for r in c.execute(text(
                "SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('bi.vw_Dim_Valores') "
                "ORDER BY column_id"))]
        assert n == len(tabelas["fato_ideia"])
        assert cols[-1] == "Faixa" and "Qual a previsão de ganho (R$) em 12 meses?" in cols
    finally:
        eng.dispose()
        banco.remover_banco("localhost", BANCO)


def test_recusa_banco_fora_do_prefixo():
    with pytest.raises(ValueError):
        banco.recriar_banco("localhost", "master")
