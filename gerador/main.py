import argparse
import secrets
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from gerador import banco
from gerador import catalogos as cat
from gerador.blocklist import CAMINHO_PROIBIDOS, carregar
from gerador.config import sortear_parametros
from gerador.fluxo import simular_todas
from gerador.ideias import derivar_campos, gerar_coautores, gerar_ganhos, gerar_ideias
from gerador.pessoas import gerar_campanhas, gerar_pessoas, gerar_unidades
from gerador.validar import validar
from gerador.valores import gerar_valores

SQL = Path(__file__).resolve().parents[1] / "sql"


def _catalogo(nomes, coluna_id: str) -> pd.DataFrame:
    return pd.DataFrame({coluna_id: range(1, len(nomes) + 1), "nome": list(nomes)})


def construir(semente: int, hoje: date, bloqueio: frozenset[str]) -> dict[str, pd.DataFrame]:
    p = sortear_parametros(semente, hoje)
    rng = np.random.default_rng(semente + 1)
    unidades = gerar_unidades(p, cat.gerar_empresas(rng, bloqueio))
    pessoas = gerar_pessoas(rng, unidades, bloqueio)
    campanhas = gerar_campanhas(unidades, p.data_inicio)
    titulos = cat.gerar_titulos(rng, p.n_ideias, bloqueio)
    ideias = gerar_ideias(rng, p, pessoas, campanhas, titulos)
    movs = simular_todas(rng, ideias, p)
    derivadas = derivar_campos(rng, ideias, movs, pessoas)
    fato = gerar_valores(rng, derivadas)
    return {
        "dim_unidade": unidades,
        "dim_pessoa": pessoas,
        "dim_campanha": campanhas,
        "dim_tema": _catalogo(cat.TEMAS, "id_tema"),
        "dim_origem": _catalogo(cat.ORIGENS, "id_origem"),
        "dim_tipo_ganho": _catalogo(cat.TIPOS_GANHO, "id_tipo_ganho"),
        "dim_motivo_reprovacao": _catalogo(cat.MOTIVOS_REPROVACAO, "id_motivo"),
        "dim_etapa": pd.DataFrame([(e.id, e.estado, e.resumo, e.terminal) for e in cat.ETAPAS],
                                  columns=["id_etapa", "estado", "resumo", "terminal"]),
        "fato_ideia": fato,
        "fato_movimentacao": movs,
        "ponte_ideia_coautor": gerar_coautores(rng, ideias, pessoas),
        "ponte_ideia_ganho": gerar_ganhos(rng, ideias, movs),
        "meta_carga": pd.DataFrame({"data_referencia": [hoje], "semente": [semente]}),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gera dados fictícios e carrega no SQL Server")
    ap.add_argument("--servidor", default="localhost")
    ap.add_argument("--banco", default="IdeiasDemo")
    ap.add_argument("--semente", type=int, default=None)
    ap.add_argument("--data-referencia", type=date.fromisoformat, default=None,
                    help="último dia dos dados (AAAA-MM-DD); padrão: hoje. Ex.: fim de mês para prints")
    ap.add_argument("--sem-blocklist", action="store_true", help="só para testes locais")
    a = ap.parse_args(argv)
    semente = a.semente if a.semente is not None else secrets.randbelow(2**31)
    bloqueio = frozenset() if a.sem_blocklist else carregar() | carregar(CAMINHO_PROIBIDOS)
    hoje = a.data_referencia or date.today()
    print(f"semente={semente} hoje={hoje}")
    tabelas = construir(semente, hoje, bloqueio)
    erros = validar(tabelas, hoje, bloqueio)
    if erros:
        print("VALIDAÇÃO FALHOU:\n  " + "\n  ".join(erros))
        return 1
    banco.recriar_banco(a.servidor, a.banco)
    eng = banco.criar_engine(a.servidor, a.banco)
    banco.executar_script(eng, SQL / "01_schema.sql")
    banco.gravar(eng, tabelas)
    banco.executar_script(eng, SQL / "03_views_compat.sql")
    falhas = banco.rodar_checks(eng, SQL / "04_checks.sql")
    if falhas:
        print("CHECKS SQL FALHARAM: " + ", ".join(falhas))
        return 1
    for nome, df in tabelas.items():
        print(f"  {nome}: {len(df)} linhas")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
