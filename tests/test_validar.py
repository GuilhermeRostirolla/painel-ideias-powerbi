from datetime import date, timedelta

from gerador.blocklist import hash_texto
from gerador.main import construir
from gerador.validar import validar

HOJE = date(2026, 9, 30)


def test_dados_gerados_passam_varias_sementes():
    for s in (1, 2, 3, 42, 2026):
        t = construir(s, HOJE, frozenset())
        assert validar(t, HOJE, frozenset()) == [], f"semente {s}"


def test_detecta_nome_bloqueado():
    t = construir(1, HOJE, frozenset())
    bl = frozenset({hash_texto(t["dim_pessoa"].nome.iloc[0])})
    assert any("bloquead" in e for e in validar(t, HOJE, bl))


def test_detecta_data_futura():
    t = construir(1, HOJE, frozenset())
    m = t["fato_movimentacao"]
    m.loc[m.index[0], "data_entrada"] = HOJE + timedelta(days=3)
    assert any("futur" in e for e in validar(t, HOJE, frozenset()))


def test_detecta_titulo_duplicado():
    t = construir(1, HOJE, frozenset())
    f = t["fato_ideia"]
    f.loc[f.index[1], "titulo"] = f.titulo.iloc[0]
    assert any("titulo" in e for e in validar(t, HOJE, frozenset()))
