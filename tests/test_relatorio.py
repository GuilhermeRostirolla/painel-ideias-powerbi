import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import aplicar_visual as av  # noqa: E402
import religar_pbip as r  # noqa: E402


def test_liberar_periodo_remove_datas_fixas():
    v = {"visual": {"visualType": "slicer", "objects": {
        "data": [{"properties": {"startDate": 1, "endDate": 2, "mode": "Between"}}],
        "general": [{"properties": {"filter": {"From": [{"Entity": "dCalendario"}]}, "outlineWeight": 1}}],
    }}}
    assert av.liberar_periodo(v)
    assert v["visual"]["objects"]["data"][0]["properties"] == {"mode": "Between"}
    assert v["visual"]["objects"]["general"][0]["properties"] == {"outlineWeight": 1}


def test_liberar_periodo_ignora_outros_slicers():
    v = {"visual": {"visualType": "slicer", "objects": {"general": [{"properties": {"filter": {
        "From": [{"Entity": "Sel_Etapa"}]}}}]}}}
    assert not av.liberar_periodo(v)


def test_limitar_eixo_evolucao():
    v = {"visual": {"visualType": "lineChart", "query": {"Property": "Evo Criadas"}, "objects": {}}}
    assert av.limitar_eixo_evolucao(v)
    fim = v["visual"]["objects"]["valueAxis"][0]["properties"]["end"]
    assert fim["expr"]["Measure"]["Property"] == "Evo Eixo Max"


def test_adicionar_medidas_layout_idempotente():
    t = "table Fato_Ideias\n\n\tmeasure A = 1\n\t\tlineageTag: x\n"
    s = r.adicionar_medidas_layout(t)
    assert s.index("measure 'Evo Eixo Max'") < s.index("measure A =")
    assert r.adicionar_medidas_layout(s).count("Evo Eixo Max'") == 1


def test_alargar_coluna_empresa():
    def col(m, w):
        return {"selector": {"metadata": m}, "properties": {"value": {"expr": {"Literal": {"Value": w}}}}}
    v = {"visual": {"objects": {"columnWidth": [col("F.Ideia", "250D"), col("F.Empresa_Sigla", "60D"),
                                                 col("F.Data", "64D")]}}}
    assert av.alargar_coluna_empresa(v)
    w = [c["properties"]["value"]["expr"]["Literal"]["Value"] for c in v["visual"]["objects"]["columnWidth"]]
    assert w == ["236.0D", "74.0D", "64D"]
    assert not av.alargar_coluna_empresa(v)
