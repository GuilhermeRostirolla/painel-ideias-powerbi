import json
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dependencias_pbip  # noqa: E402
import metas  # noqa: E402

NOME = "PainelIdeias"
NOVA = "Fato_Ideias"

VIEWS = {
    NOVA: "vw_Fato_Ideias", "Dim_Estado": "vw_Dim_Estado", "Dim_Tema": "vw_Dim_Tema",
    "Dim_Colaboradores": "vw_Dim_Colaboradores", "Dim_Elaborador": "vw_Dim_Elaborador",
    "Dim_SLA_Ideias": "vw_Dim_SLA_Ideias", "Dim_Valores": "vw_Dim_Valores",
    "Dim_Data": "vw_Dim_Data", "Dim_Empresa_Campanha": "vw_Dim_Empresa_Campanha",
    "Dim_Ganhos_Indiretos": "vw_Dim_Ganhos_Indiretos", "Planilha": "vw_Planilha",
}
MANTER_COLUNAS = {
    "Dim_Ganhos_Indiretos": {"Primaria_Key", "Ganhos_Indiretos"},
}
_FIM_EXPR = (r"(?=^\t\t(?:dataType|formatString|lineageTag|summarizeBy|displayFolder|isHidden"
             r"|annotation|sortByColumn|dataCategory)\b)")
_CORPO = r"(?:(?:\t\t[^\n]*)?\n)*"


def particao_sql(tabela: str, view: str) -> str:
    return (f"\tpartition {tabela} = m\n\t\tmode: import\n\t\tsource =\n"
            f"\t\t\t\tlet\n"
            f"\t\t\t\t    Fonte = Sql.Database(\"localhost\", \"IdeiasDemo\"),\n"
            f"\t\t\t\t    Dados = Fonte{{[Schema=\"bi\", Item=\"{view}\"]}}[Data]\n"
            f"\t\t\t\tin\n\t\t\t\t    Dados\n\n")


def substituir_particao(tmdl: str, tabela: str, view: str) -> str:
    padrao = re.compile(r"^\tpartition [^\n]*\n" + _CORPO, re.M)
    novo, n = padrao.subn(lambda _: particao_sql(tabela, view), tmdl, count=1)
    if n != 1:
        raise ValueError(f"partição não encontrada em {tabela}")
    return novo


def remover_colunas(tmdl: str, manter: set[str]) -> str:
    bloco = re.compile(r"^\tcolumn (?P<nome>'[^'\n]+'|[^\n=]+?)[ \t]*\n(?P<corpo>" + _CORPO + ")", re.M)

    def talvez(m: re.Match) -> str:
        nome = m.group("nome").strip().strip("'")
        eh_base = "sourceColumn:" in m.group("corpo")
        return m.group(0) if (nome in manter or not eh_base) else ""

    return bloco.sub(talvez, tmdl)


def substituir_expressao_coluna(tmdl: str, coluna: str, nova: str) -> str:
    padrao = re.compile(rf"^\tcolumn {re.escape(coluna)} =.*?{_FIM_EXPR}", re.M | re.S)
    novo, n = padrao.subn(lambda _: f"\tcolumn {coluna} = {nova}\n", tmdl, count=1)
    if n != 1:
        raise ValueError(f"coluna calculada {coluna} não encontrada")
    return novo


def neutralizar_dax(tmdl: str) -> str:
    tmdl = re.sub(
        r"(VAR\s+(?:UnidadePlanilha|MapeamentoUnidade)\s*=\s*)SWITCH\s*\(\s*(\w+)\s*,"
        r"(?:\s*\"[^\"]*\"\s*,\s*\"[^\"]*\"\s*,?)+\s*\)",
        lambda m: (f"{m.group(1)}MAXX ( FILTER ( ALL ( Dim_Empresa_Campanha ), "
                   f"Dim_Empresa_Campanha[Abreviação] = {m.group(2)} ), "
                   f"Dim_Empresa_Campanha[Empresa] )"), tmdl)
    tmdl = re.sub(
        r"SUBSTITUTE\s*\(\s*((?:RELATED\s*\(\s*)?Dim_Empresa_Campanha\[Abreviação\](?:\s*\))?)"
        r"\s*,\s*\"[^\"]*\"\s*,\s*\"[^\"]*\"\s*\)",
        lambda m: m.group(1), tmdl)
    antigo = "Ideia" + chr(38) + "Ação"
    return tmdl.replace(f"_Design {antigo}", "_Design").replace(antigo, "Programa de Ideias")


def definir_metas(tmdl: str) -> str:
    tmdl, n1 = re.subn(r"(\tmeasure 'Eng Meta' = )[\d.]+", rf"\g<1>{metas.META_ENGAJAMENTO}", tmdl)
    tmdl, n2 = re.subn(r"(\tmeasure 'SLA Referência \(dias\)' = )\d+",
                       rf"\g<1>{metas.SLA_GERAL_DIAS}", tmdl)
    if n1 != 1 or n2 != 1:
        raise ValueError("medidas de meta não encontradas")
    if "measure 'SLA Etapa (dias)'" not in tmdl:
        casos = ", ".join(f'"{e}", {d}' for e, d in metas.SLA_ETAPA_DIAS.items())
        novas = (f"\tmeasure 'SLA Etapa (dias)' = SWITCH ( SELECTEDVALUE ( Sel_Etapa[Etapa] ), "
                 f"{casos}, [SLA Referência (dias)] )\n\t\tformatString: 0\n"
                 f"\t\tdisplayFolder: _Design\n\t\tlineageTag: {uuid.uuid4()}\n\n")
        ancora = "\tmeasure 'SLA Referência (dias)'"
        tmdl = tmdl.replace(ancora, novas + ancora, 1)
    return tmdl.replace("[Tempo Etapa Sel] > [SLA Referência (dias)]",
                        "[Tempo Etapa Sel] > [SLA Etapa (dias)]")


_TXT_MOEDA = ('VAR __v = {base} + 0 RETURN IF ( __v >= 1000000, "R$ " & FORMAT ( __v / 1000000, '
              '"0.0" ) & " mi", "R$ " & FORMAT ( __v / 1000, "#,0" ) & " mil" )')


def _trocar_medida(tmdl: str, nome: str, expressao: str, formato: str | None = None) -> str:
    padrao = re.compile(rf"(\tmeasure '{re.escape(nome)}' = )[^\n]*\n((?:\t\t[^\n]*\n)*)")
    m = padrao.search(tmdl)
    if not m:
        raise ValueError(f"medida {nome} não encontrada")
    corpo = m.group(2)
    if formato is not None:
        corpo = re.sub(r"\t\tformatString: [^\n]*\n", "", corpo)
        corpo = f"\t\tformatString: {formato}\n" + corpo
    return tmdl[:m.start()] + f"{m.group(1)}{expressao}\n{corpo}" + tmdl[m.end():]


MEDIDAS_LAYOUT = {
    "Evo Eixo Max": "MAXX ( VALUES ( dCalendario[AnoMes] ), "
                    "MAX ( [Evo Criadas] + 0, [Evo Implantadas] + 0 ) ) * 1.25",
}


CORRECOES_MEDIDAS = {
    "Onde Max": "MAX ( MAXX ( ALL ( Fato_Ideias[Etapa_Atual], Fato_Ideias[Etapa_Atual_Ordem] ), "
                "[Valor Previsto] + 0 ), 1 )",
    "Txt Engajamento Colab": 'FORMAT ( [Qtd_Engajados], "#,0" ) & " de " & '
                             'FORMAT ( [Qtd_Funcionarios], "#,0" ) & " participaram"',
}


FORMATOS = {"KPI Tempo Avaliação": '0" d"', "KPI Tempo Proposta": '0" d"', "KPI Ideias por Autor": "0"}


def _trocar_formato(tmdl: str, nome: str, formato: str) -> str:
    padrao = re.compile(rf"(\tmeasure (?:'{re.escape(nome)}'|{re.escape(nome)}) =[^\n]*\n"
                        rf"(?:\t\t(?!formatString)[^\n]*\n)*)\t\tformatString: [^\n]*\n", re.M)
    novo, n = padrao.subn(lambda m: f"{m.group(1)}\t\tformatString: {formato}\n", tmdl, count=1)
    if n != 1:
        raise ValueError(f"formato da medida {nome} não encontrado")
    return novo


def corrigir_medidas(tmdl: str) -> str:
    for nome, expr in CORRECOES_MEDIDAS.items():
        tmdl = _trocar_medida(tmdl, nome, expr)
    for nome, formato in FORMATOS.items():
        tmdl = _trocar_formato(tmdl, nome, formato)
    return tmdl


def adicionar_medidas_layout(tmdl: str) -> str:
    for nome, expr in MEDIDAS_LAYOUT.items():
        if f"\tmeasure '{nome}' =" in tmdl:
            continue
        bloco = (f"\tmeasure '{nome}' = {expr}\n\t\tformatString: 0\n"
                 f"\t\tdisplayFolder: _Design\n\t\tlineageTag: {uuid.uuid4()}\n\n")
        i = tmdl.index("\n\tmeasure ") + 1
        tmdl = tmdl[:i] + bloco + tmdl[i:]
    return tmdl


def ajustar_financeiro(tmdl: str) -> str:
    for nome, base in (("Prev Mil", "[Valor Previsto]"), ("Inv Mil", "[Valor Investido]"),
                       ("Ganho Mil", "[Ganho Previsto 12m]")):
        tmdl = _trocar_medida(tmdl, nome, f"DIVIDE ( {base}, 1000000 ) + 0", '#,0.0" mi"')
    for nome, base in (("Txt Previsto", "[Valor Previsto]"), ("Txt Investido", "[Valor Investido]"),
                       ("Txt Ganho", "[Ganho Previsto 12m]")):
        tmdl = _trocar_medida(tmdl, nome, _TXT_MOEDA.format(base=base))
    tmdl = _trocar_medida(tmdl, "Txt Onde Valor",
                          '"R$ " & FORMAT ( DIVIDE ( [Valor Previsto] + 0, 1000000 ), "0.0" ) & " mi"')
    col = re.compile(r"(\tcolumn Investido_Idea = [^\n]*?)( \+ 0)?\n(\t\tdataType: double\n)"
                     r"\t\tformatString: [^\n]*\n")
    tmdl, n = col.subn(lambda m: f"{m.group(1)} + 0\n{m.group(3)}\t\tformatString: #,0;-#,0;—\n", tmdl)
    if n != 1:
        raise ValueError("coluna Investido_Idea não encontrada")
    return tmdl


HOJE_REF = "MAX ( Referencia[Hoje] )"


def fixar_data_referencia(tmdl: str) -> str:
    return re.sub(r"\bTODAY\s*\(\s*\)", HOJE_REF, tmdl)


def _tabela_referencia() -> str:
    g = lambda: str(uuid.uuid4())  # noqa: E731
    return (f"table Referencia\n\tisHidden\n\tlineageTag: {g()}\n\n"
            f"\tcolumn Hoje\n\t\tdataType: dateTime\n\t\tisHidden\n\t\tformatString: Short Date\n"
            f"\t\tlineageTag: {g()}\n\t\tsummarizeBy: none\n\t\tsourceColumn: Hoje\n\n"
            + particao_sql("Referencia", "vw_Referencia")
            + "\tannotation PBI_ResultType = Table\n")


def papeis_por_empresa(empresas: list[tuple[str, str]]) -> dict[str, dict[str, str]]:
    return {sigla: {"Dim_Empresa_Campanha": f'[Abreviação] = "{sigla}"',
                    "Planilha": f'[Unidade de Prestação Serviço] = "{nome}"',
                    "TabelaFuncionarios": f'[Empresa] = "{sigla}"'}
            for nome, sigla in empresas}


def _ref_papel(nome: str) -> str:
    return f"'{nome}'" if re.search(r"\W", nome) else nome


def _papel(nome: str, filtros: dict[str, str]) -> str:
    corpo = "".join(f"\n\ttablePermission {t} = {expr}\n" for t, expr in filtros.items())
    return f"role {_ref_papel(nome)}\n\tmodelPermission: read\n" + corpo


def adicionar_rls(raiz: Path, empresas: list[tuple[str, str]]) -> None:
    sm = raiz / f"{NOME}.SemanticModel" / "definition"
    pasta = sm / "roles"
    pasta.mkdir(exist_ok=True)
    for antigo in pasta.glob("*.tmdl"):
        antigo.unlink()
    papeis = papeis_por_empresa(empresas)
    for nome, filtros in papeis.items():
        (pasta / f"{nome}.tmdl").write_text(_papel(nome, filtros), encoding="utf-8")
    model = sm / "model.tmdl"
    linhas = [x for x in model.read_text(encoding="utf-8-sig").splitlines(keepends=True)
              if not x.startswith("ref role ")]
    refs = "".join(f"ref role {_ref_papel(n)}\n" for n in papeis)
    s = "".join(linhas).replace("ref cultureInfo", refs + "\nref cultureInfo", 1)
    model.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")


def empresas_do_banco(servidor: str = "localhost", banco: str = "IdeiasDemo") -> list[tuple[str, str]]:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from sqlalchemy import text

    from gerador.banco import criar_engine
    with criar_engine(servidor, banco).connect() as c:
        return [(n, s) for n, s in c.execute(text("SELECT nome, sigla FROM dw.dim_unidade ORDER BY sigla"))]


def _sem_uso(sm_tabelas: Path, rep_dir: Path) -> tuple[set[str], set[tuple[str, str]]]:
    objs, calc, tabelas = dependencias_pbip.carregar(sm_tabelas)
    vistos = dependencias_pbip.usados(objs, calc, rep_dir)
    while True:
        mantidas = {t for t, _ in vistos}
        extras = {(t, n) for (t, n), (k, _) in objs.items()
                  if k == "column" and t in mantidas and (t, n) not in vistos}
        if not extras:
            break
        vistos |= dependencias_pbip.fechamento(extras, objs, calc)
    tabelas_sem_uso = set(tabelas) - {t for t, _ in vistos}
    medidas_sem_uso = {(t, n) for (t, n), (k, _) in objs.items()
                       if k == "measure" and (t, n) not in vistos and t not in tabelas_sem_uso}
    return tabelas_sem_uso, medidas_sem_uso


def _remover_medida(tmdl: str, nome: str) -> str:
    nome_re = re.escape(nome)
    padrao = re.compile(rf"^\tmeasure (?:'{nome_re}'|{nome_re}) =[^\n]*\n{_CORPO}", re.M)
    novo, n = padrao.subn("", tmdl, count=1)
    if n != 1:
        raise ValueError(f"medida {nome} não encontrada para remoção")
    return novo


def remover_sem_uso(raiz: Path) -> tuple[set[str], set[tuple[str, str]]]:
    sm = raiz / f"{NOME}.SemanticModel"
    tabelas_dir = sm / "definition" / "tables"
    tabelas, medidas = _sem_uso(tabelas_dir, raiz / f"{NOME}.Report" / "definition")
    for arq in tabelas_dir.glob("*.tmdl"):
        t = arq.read_text(encoding="utf-8-sig").splitlines()[0][6:].strip().strip("'")
        if t in tabelas:
            arq.unlink()
            continue
        s = arq.read_text(encoding="utf-8-sig")
        for tab, nome in medidas:
            if tab == t:
                s = _remover_medida(s, nome)
        s = re.sub(r"^\t\tvariation [^\n]*\n(?:\t\t\t[^\n]*\n|\n(?=\t\t\t))*", "", s, flags=re.M)
        arq.write_text(s, encoding="utf-8")

    rel = sm / "definition" / "relationships.tmdl"
    blocos = re.split(r"(?=^relationship )", rel.read_text(encoding="utf-8-sig"), flags=re.M)
    nomes_re = [re.escape(t) for t in tabelas]
    manter = [b for b in blocos
              if not any(re.search(rf"Column: '?{n}'?\.", b) for n in nomes_re)]
    rel.write_text("".join(manter), encoding="utf-8")

    model = sm / "definition" / "model.tmdl"
    linhas = [linha for linha in model.read_text(encoding="utf-8-sig").splitlines(keepends=True)
              if not (linha.startswith("ref table ")
                      and linha[10:].strip().strip("'") in tabelas)]
    s = "".join(linhas).replace("__PBI_TimeIntelligenceEnabled = 1", "__PBI_TimeIntelligenceEnabled = 0")
    model.write_text(s, encoding="utf-8")

    diagrama = sm / "diagramLayout.json"
    if diagrama.exists():
        d = json.loads(diagrama.read_text(encoding="utf-8-sig"))
        for dg in d.get("diagrams", []):
            dg["nodes"] = [n for n in dg.get("nodes", []) if n.get("nodeIndex") not in tabelas]
        diagrama.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return tabelas, medidas


def _colunas_estruturais(sm: Path, tabelas: dict[str, Path]) -> set[tuple[str, str]]:
    rel = (sm / "relationships.tmdl").read_text(encoding="utf-8-sig")
    fixas = {(t.strip("'"), c.strip("'"))
             for t, c in re.findall(r"Column: ('[^']+'|[^.\s]+)\.('[^']+'|\S+)", rel)}
    for t, arq in tabelas.items():
        s = arq.read_text(encoding="utf-8-sig")
        for c in re.findall(r"^\t\t(?:sortByColumn|\tcolumn): ('[^']+'|\S+)", s, flags=re.M):
            fixas.add((t, c.strip("'")))
    for papel in (sm / "roles").glob("*.tmdl") if (sm / "roles").exists() else []:
        for t, expr in re.findall(r"^\ttablePermission ('[^']+'|\S+) = ([^\n]+)",
                                  papel.read_text(encoding="utf-8-sig"), flags=re.M):
            t = t.strip("'")
            fixas |= {(t, c) for c in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", expr)}
            fixas |= {(o.strip("'"), c) for o, c in re.findall(r"('[^']+'|\w+)\[([^\]]+)\]", expr)}
    return fixas


def colunas_sem_uso(sm_tabelas: Path, rep_dir: Path) -> dict[str, set[str]]:
    objs, calc, tabelas = dependencias_pbip.carregar(sm_tabelas)
    vistos = dependencias_pbip.usados(objs, calc, rep_dir)
    fixas = _colunas_estruturais(sm_tabelas.parent, tabelas)
    sem_uso = {}
    for t, arq in tabelas.items():
        s = arq.read_text(encoding="utf-8-sig")
        if re.search(r"^\tpartition [^\n]*= calculated", s, flags=re.M):
            continue
        nomes = {c.strip("'") for c in re.findall(r"^\tcolumn ('[^']+'|[^\s=]+)", s, flags=re.M)}
        sobra = {c for c in nomes if (t, c) not in vistos and (t, c) not in fixas}
        if sobra:
            sem_uso[t] = sobra
    return sem_uso


def remover_coluna(tmdl: str, nome: str) -> tuple[str, str | None]:
    nome_re = re.escape(nome)
    padrao = re.compile(rf"^\tcolumn (?:'{nome_re}'|{nome_re})(?=[ \t]*(?:=|\n))[^\n]*\n{_CORPO}", re.M)
    m = padrao.search(tmdl)
    if not m:
        raise ValueError(f"coluna {nome} não encontrada para remoção")
    fonte = re.search(r"^\t\tsourceColumn: ([^\n]+)", m.group(0), flags=re.M)
    return tmdl[:m.start()] + tmdl[m.end():], fonte.group(1).strip() if fonte else None


def remover_colunas_sem_uso(raiz: Path) -> dict[str, dict[str, str | None]]:
    tabelas_dir = raiz / f"{NOME}.SemanticModel" / "definition" / "tables"
    removidas = {}
    for t, nomes in colunas_sem_uso(tabelas_dir, raiz / f"{NOME}.Report" / "definition").items():
        arq = tabelas_dir / f"{t}.tmdl"
        s = arq.read_text(encoding="utf-8-sig")
        removidas[t] = {}
        for nome in sorted(nomes):
            s, fonte = remover_coluna(s, nome)
            removidas[t][nome] = fonte
        arq.write_text(s, encoding="utf-8")
    return removidas


def limpar_model(model: str) -> str:
    return "".join(linha for linha in model.splitlines(keepends=True)
                   if not linha.startswith(("ref role ", "ref culture ")))


def _tabela_funcionarios() -> str:
    g = lambda: str(uuid.uuid4())  # noqa: E731
    return (f"table TabelaFuncionarios\n\tlineageTag: {g()}\n\n"
            f"\tcolumn Empresa\n\t\tdataType: string\n\t\tlineageTag: {g()}\n"
            f"\t\tsummarizeBy: none\n\t\tsourceColumn: Empresa\n\n"
            f"\tcolumn Funcionarios\n\t\tdataType: int64\n\t\tformatString: 0\n"
            f"\t\tlineageTag: {g()}\n\t\tsummarizeBy: sum\n\t\tsourceColumn: Funcionarios\n\n"
            + particao_sql("TabelaFuncionarios", "vw_TabelaFuncionarios")
            + "\tannotation PBI_ResultType = Table\n")


def _textos(raiz: Path):
    for p in raiz.rglob("*"):
        if p.is_file() and (p.suffix in {".tmdl", ".json", ".pbir", ".pbism", ".pbip"}
                            or p.name == ".platform"):
            yield p


def religar(raiz: Path) -> list[str]:
    sm = raiz / f"{NOME}.SemanticModel" / "definition"
    tabelas = sm / "tables"

    antiga_arq = next((p for p in tabelas.glob("Fato_*.tmdl") if p.stem != NOVA), None)
    if antiga_arq:
        antiga = antiga_arq.stem
        for p in _textos(raiz):
            s = p.read_text(encoding="utf-8-sig")
            if antiga in s:
                p.write_text(s.replace(antiga, NOVA), encoding="utf-8")
        antiga_arq.rename(tabelas / f"{NOVA}.tmdl")

    tabelas_removidas, medidas_removidas = remover_sem_uso(raiz)
    print(f"removidas: {len(tabelas_removidas)} tabelas e {len(medidas_removidas)} medidas sem uso")

    for tabela, view in VIEWS.items():
        arq = tabelas / f"{tabela}.tmdl"
        s = substituir_particao(arq.read_text(encoding="utf-8-sig"), tabela, view)
        if tabela in MANTER_COLUNAS:
            s = remover_colunas(s, MANTER_COLUNAS[tabela])
        arq.write_text(s, encoding="utf-8")

    fato = tabelas / f"{NOVA}.tmdl"
    s = substituir_expressao_coluna(fato.read_text(encoding="utf-8"), "Tema_Curto",
                                    "RELATED ( Dim_Tema[Nome_tema] )")
    s = adicionar_medidas_layout(corrigir_medidas(ajustar_financeiro(definir_metas(s))))
    fato.write_text(s, encoding="utf-8")
    ganhos = tabelas / "Dim_Ganhos_Indiretos.tmdl"
    ganhos.write_text(substituir_expressao_coluna(ganhos.read_text(encoding="utf-8"), "Ganho_Curto",
                                                  "Dim_Ganhos_Indiretos[Ganhos_Indiretos]"), encoding="utf-8")
    (tabelas / "TabelaFuncionarios.tmdl").write_text(_tabela_funcionarios(), encoding="utf-8")

    for arq in tabelas.glob("*.tmdl"):
        s = arq.read_text(encoding="utf-8-sig")
        arq.write_text(fixar_data_referencia(neutralizar_dax(s)), encoding="utf-8")
    (tabelas / "Referencia.tmdl").write_text(_tabela_referencia(), encoding="utf-8")
    model = sm / "model.tmdl"
    s = limpar_model(model.read_text(encoding="utf-8-sig"))
    if "ref table Referencia" not in s:
        s = s.replace(f"ref table {NOVA}\n", f"ref table {NOVA}\nref table Referencia\n", 1)
    model.write_text(s, encoding="utf-8")
    colunas = remover_colunas_sem_uso(raiz)
    print(f"removidas: {sum(map(len, colunas.values()))} colunas sem uso")

    residuos = []
    padrao = re.compile(r"https?://|token=|\.xlsx|Share" r"Point|Web\.Contents", re.I)
    for p in _textos(raiz):
        for i, linha in enumerate(p.read_text(encoding="utf-8-sig").splitlines(), 1):
            if padrao.search(linha) and "schema" not in linha.lower():
                residuos.append(f"{p.relative_to(raiz)}:{i}: {linha.strip()[:80]}")
    return residuos


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[1] / "powerbi"
    if "--rls" in sys.argv:
        empresas = empresas_do_banco()
        adicionar_rls(raiz, empresas)
        print("RLS: 1 papel por empresa ->", ", ".join(s for _, s in empresas))
        sys.exit(0)
    r = religar(raiz)
    if r:
        print("RESÍDUOS:\n  " + "\n  ".join(r))
        sys.exit(1)
    print("OK: modelo religado ao SQL")
