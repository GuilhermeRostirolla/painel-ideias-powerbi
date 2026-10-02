import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import religar_pbip as r  # noqa: E402

ANTIGO = "Ideia" + chr(38) + "Ação"

TMDL = (
    "table Dim_Tema\n"
    "\tlineageTag: x\n\n"
    "\tcolumn ID_Tema\n\t\tdataType: string\n\t\tsourceColumn: ID_Tema\n\n"
    "\tcolumn 'Pergunta longa?'\n\t\tdataType: string\n\t\tsourceColumn: Pergunta longa?\n\n"
    "\tcolumn Curto = ```\n\t\t\tSWITCH ( [A], \"x\", \"y\" )\n\t\t\t```\n"
    "\t\tlineageTag: z\n\n"
    "\tpartition Dim_Tema = m\n\t\tmode: import\n\t\tsource =\n"
    "\t\t\t\tlet\n\t\t\t\t    urlBase = \"https://exemplo/api?token=abc\"\n\t\t\t\tin\n"
    "\t\t\t\t    urlBase\n\n"
    "\tannotation PBI_ResultType = Table\n"
)


def test_substituir_particao():
    s = r.substituir_particao(TMDL, "Dim_Tema", "vw_Dim_Tema")
    assert "token" not in s and 'Item="vw_Dim_Tema"' in s
    assert 'Sql.Database("localhost", "IdeiasDemo")' in s
    assert s.count("\tpartition ") == 1 and "annotation PBI_ResultType" in s


def test_remover_colunas_mantem_calculadas():
    s = r.remover_colunas(TMDL, {"ID_Tema"})
    assert "Pergunta longa?" not in s and "column ID_Tema" in s and "column Curto =" in s


def test_substituir_expressao_coluna():
    s = r.substituir_expressao_coluna(TMDL, "Curto", "Dim_Tema[ID_Tema]")
    assert "\tcolumn Curto = Dim_Tema[ID_Tema]\n\t\tlineageTag: z" in s and "SWITCH" not in s


def test_neutralizar_dax_mapeamento_e_substitute():
    dax = ('VAR UnidadePlanilha = SWITCH( Abrev, "AAA", "EMPRESA X", "BBB", "EMPRESA Y" )\n'
           'x = SUBSTITUTE ( RELATED ( Dim_Empresa_Campanha[Abreviação] ), "Q", "W" )\n'
           'displayFolder: _Design ' + ANTIGO)
    s = r.neutralizar_dax(dax)
    assert ("VAR UnidadePlanilha = MAXX ( FILTER ( ALL ( Dim_Empresa_Campanha ), "
            "Dim_Empresa_Campanha[Abreviação] = Abrev )") in s
    assert "EMPRESA" not in s and "SWITCH" not in s
    assert "x = RELATED ( Dim_Empresa_Campanha[Abreviação] )" in s
    assert "displayFolder: _Design" in s and ANTIGO not in s


def test_limpar_model():
    m = "model Model\n\tculture: pt-BR\n\nref table A\nref role 'X Y'\nref culture pt-BR\n"
    s = r.limpar_model(m)
    assert "ref role" not in s and "ref culture" not in s and "ref table A" in s


def test_definir_metas():
    t = ("\tmeasure 'SLA Referência (dias)' = 60\n\t\tformatString: 0\n\n"
         "\tmeasure 'Cor Tempo Etapa' = "
         "IF ( [Tempo Etapa Sel] > [SLA Referência (dias)], \"#1\", \"#2\" )\n\n"
         "\tmeasure 'Eng Meta' = 0.3\n")
    s = r.definir_metas(t)
    assert "measure 'Eng Meta' = 0.5" in s
    assert "measure 'SLA Etapa (dias)' = SWITCH ( SELECTEDVALUE ( Sel_Etapa[Etapa] ), \"Avaliação\", 15" in s
    assert "[Tempo Etapa Sel] > [SLA Etapa (dias)]" in s and "Meta Conversão" not in s
    assert r.definir_metas(s).count("measure 'SLA Etapa (dias)'") == 1


FIN = "".join(
    f"\tmeasure '{n}' = X\n\t\tformatString: #,0\n\t\tlineageTag: a\n\n"
    for n in ("Prev Mil", "Inv Mil", "Ganho Mil", "Txt Previsto", "Txt Investido", "Txt Ganho",
              "Txt Onde Valor")) + (
    "\tcolumn Investido_Idea = SUMX ( T, T[x] )\n\t\tdataType: double\n\t\tformatString: #,0\n"
    "\t\tlineageTag: b\n")


def test_ajustar_financeiro():
    s = r.ajustar_financeiro(FIN)
    assert ("measure 'Prev Mil' = DIVIDE ( [Valor Previsto], 1000000 ) + 0\n"
            "\t\tformatString: #,0.0\" mi\"") in s
    assert s.count('& " mi"') == 4 and '"0.0"' in s and '"k"' not in s
    assert "measure 'Txt Onde Valor' = \"R$ \" & FORMAT ( DIVIDE ( [Valor Previsto] + 0, 1000000 )" in s
    assert "column Investido_Idea = SUMX ( T, T[x] ) + 0\n" in s and "formatString: #,0;-#,0;—" in s
    assert r.ajustar_financeiro(s).count("+ 0 + 0") == 0


def test_fixar_data_referencia():
    s = r.fixar_data_referencia('x = EOMONTH ( TODAY (), 0 ) & FORMAT ( TODAY(), "mmm" )')
    assert "TODAY" not in s and s.count("MAX ( Referencia[Hoje] )") == 2


def test_remover_coluna_devolve_origem():
    t = ("\tcolumn 'Com Espaço:'\n\t\tdataType: string\n\t\tsourceColumn: Origem X\n\n"
         "\t\tannotation SummarizationSetBy = Automatic\n\n"
         "\tcolumn Calc = ```\n\t\t\tSWITCH ( 1, 1, 2 )\n\t\t\t```\n\t\tlineageTag: a\n\n"
         "\tcolumn Fica\n\t\tsourceColumn: Fica\n")
    s, fonte = r.remover_coluna(t, "Com Espaço:")
    assert fonte == "Origem X" and "Com Espaço" not in s
    s, fonte = r.remover_coluna(s, "Calc")
    assert fonte is None and s == "\tcolumn Fica\n\t\tsourceColumn: Fica\n"


def test_remover_medida_com_e_sem_aspas():
    t = ("\tmeasure Taxa(%) =\n\t\t\tDIVIDE ( 1, 2 )\n\t\tlineageTag: a\n\n"
         "\tmeasure 'Com Espaço' = 1\n\t\tlineageTag: b\n\n\tmeasure Fica = 2\n")
    s = r._remover_medida(r._remover_medida(t, "Taxa(%)"), "Com Espaço")
    assert s == "\tmeasure Fica = 2\n"


def test_adicionar_rls_um_papel_por_empresa(tmp_path):
    sm = tmp_path / "PainelIdeias.SemanticModel" / "definition"
    (sm / "roles").mkdir(parents=True)
    (sm / "roles" / "Antigo.tmdl").write_text("role Antigo\n", encoding="utf-8")
    (sm / "model.tmdl").write_text("model Model\n\nref table A\nref role Antigo\n\nref cultureInfo pt-BR\n",
                                   encoding="utf-8")
    empresas = [("Litoral Embalagens", "Litoral"), ("Jatobá Serviços", "Jatobá")]
    r.adicionar_rls(tmp_path, empresas)
    r.adicionar_rls(tmp_path, empresas)
    model = (sm / "model.tmdl").read_text(encoding="utf-8")
    assert "Antigo" not in model and model.count("ref role Litoral") == 1
    assert model.count("ref role Jatobá") == 1
    assert sorted(p.stem for p in (sm / "roles").glob("*.tmdl")) == ["Jatobá", "Litoral"]
    litoral = (sm / "roles" / "Litoral.tmdl").read_text(encoding="utf-8")
    assert 'tablePermission Dim_Empresa_Campanha = [Abreviação] = "Litoral"' in litoral
    assert '[Unidade de Prestação Serviço] = "Litoral Embalagens"' in litoral
