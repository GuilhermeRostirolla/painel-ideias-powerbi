import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

PREFIXO = "IdeiasDemo"
SCHEMA_DADOS = "dw"
_DRIVER = "ODBC+Driver+18+for+SQL+Server"


def _url(servidor: str, banco: str) -> str:
    return (f"mssql+pyodbc://@{servidor}/{banco}?driver={_DRIVER}"
            "&trusted_connection=yes&TrustServerCertificate=yes")


def criar_engine(servidor: str, banco: str) -> Engine:
    return create_engine(_url(servidor, banco), fast_executemany=True)


def _checar_nome(banco: str) -> None:
    if not re.fullmatch(rf"{PREFIXO}\w*", banco):
        raise ValueError(f"banco '{banco}' fora do prefixo {PREFIXO}: recusado")


def remover_banco(servidor: str, banco: str) -> None:
    _checar_nome(banco)
    eng = create_engine(_url(servidor, "master"), isolation_level="AUTOCOMMIT")
    with eng.connect() as c:
        c.execute(text(f"IF DB_ID('{banco}') IS NOT NULL BEGIN "
                       f"ALTER DATABASE [{banco}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
                       f"DROP DATABASE [{banco}]; END"))
    eng.dispose()


def recriar_banco(servidor: str, banco: str) -> None:
    remover_banco(servidor, banco)
    eng = create_engine(_url(servidor, "master"), isolation_level="AUTOCOMMIT")
    with eng.connect() as c:
        c.execute(text(f"CREATE DATABASE [{banco}]"))
    eng.dispose()


def executar_script(engine: Engine, caminho: Path) -> None:
    lotes = re.split(r"^\s*GO\s*$", caminho.read_text(encoding="utf-8"), flags=re.M)
    with engine.begin() as c:
        for lote in lotes:
            if lote.strip():
                c.exec_driver_sql(lote)


def _para_sql(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(object).where(df.notna(), None)


def gravar(engine: Engine, tabelas: dict[str, pd.DataFrame]) -> None:
    with engine.begin() as c:
        for nome, df in tabelas.items():
            if nome == "dim_pessoa":
                df = df.sort_values("eh_gestor", ascending=False, kind="stable")
            _para_sql(df).to_sql(nome, c, schema=SCHEMA_DADOS, if_exists="append", index=False,
                                 chunksize=2000)


def rodar_checks(engine: Engine, caminho: Path) -> list[str]:
    with engine.connect() as c:
        linhas = c.exec_driver_sql(caminho.read_text(encoding="utf-8")).fetchall()
    return [nome for nome, ok in linhas if ok != 1]
