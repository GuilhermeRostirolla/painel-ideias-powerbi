import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cores  # noqa: E402
import metas  # noqa: E402

NOME = "PainelIdeias"
TITULO_PROGRAMA = "PROGRAMA DE IDEIAS"
PAGINAS = {"Fundo_geral.png": "Visão Geral", "Fundo_sla.png": "SLA & Fluxo",
           "Fundo_implantadas.png": "Implantadas", "Fundo_financeiro.png": "Financeiro",
           "Fundo_colaboradores.png": "Colaboradores", "Fundo_ideias.png": "Detalhe das Ideias"}
FAIXA_TITULO = (0.06, 0.45)
GRADIENTE = ((0x17, 0x3E, 0x4C), (0x2F, 0x7A, 0x8C))
FONTE = r"C:\Windows\Fonts\segoeui.ttf"
FONTE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONTE_SEMI = r"C:\Windows\Fonts\seguisb.ttf"
_SLA = metas.SLA_ETAPA_DIAS
TEXTOS_FUNDO = {
    "Fundo_sla.png": [
        ("pilula", (425, 143, 549, 171), f"SLA {_SLA['Avaliação']} d"),
        ("pilula", (893, 143, 1017, 171), f"SLA {_SLA['Proposta de Solução']} d"),
        ("legenda", (148, 764, 470, 785),
         f"Dias · âmbar = acima do SLA da etapa · tracejado = SLA geral ({metas.SLA_GERAL_DIAS} d)"),
    ],
    "Fundo_geral.png": [("pilula", (1820, 143, 1955, 171), f"meta {metas.pct(metas.META_ENGAJAMENTO)}")],
    "Fundo_financeiro.png": [
        ("legenda", (148, 355, 200, 374), "R$ milhões"),
        ("legenda", (1272, 764, 1552, 784), "Por status · clique para filtrar"),
    ],
    "Fundo_implantadas.png": [("pilula", (1196, 143, 1329, 171), f"meta {metas.pct(metas.META_CONVERSAO)}")],
    "Fundo_colaboradores.png": [
        ("pilula", (415, 143, 548, 171), f"meta {metas.pct(metas.META_ENGAJAMENTO)}"),
        ("legenda", (1205, 355, 1720, 375),
         f"Colaboradores com ideia ÷ total · meta de {metas.pct(metas.META_ENGAJAMENTO)}"),
    ],
}
COR_TEXTO_PILULA = (60, 75, 87, 255)
COR_LEGENDA = (95, 107, 122, 255)


def _reescrever(img: Image.Image, tipo: str, caixa_tela, texto: str) -> None:
    k = img.width / 2000
    x0, y0, x1, y1 = (round(v * k) for v in caixa_tela)
    ym = (y0 + y1) // 2
    d = ImageDraw.Draw(img)
    fundo = img.getpixel((x0 - round(6 * k), ym))
    if tipo == "pilula":
        cor_pilula = img.getpixel((x0 + round(4 * k), ym))
        d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), fill=fundo)
        f = ImageFont.truetype(FONTE_SEMI, round((y1 - y0) * 0.62))
        pad = round(12 * k)
        largura = d.textlength(texto, font=f) + 2 * pad
        d.rounded_rectangle((x1 - largura, y0, x1, y1), radius=(y1 - y0) // 2, fill=cor_pilula)
        d.text((x1 - largura / 2, ym), texto, font=f, fill=COR_TEXTO_PILULA, anchor="mm")
    else:
        d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), fill=fundo)
        f = ImageFont.truetype(FONTE, round((y1 - y0) * 0.82))
        d.text((x0, ym), texto, font=f, fill=COR_LEGENDA, anchor="lm")
TEMA = {
    "name": "Painel de Ideias",
    "dataColors": ["#1F4E5F", "#E0A100", "#5B7A89", "#A9BCC6", "#2F7A8C", "#B37F00",
                   "#8FA9B5", "#1B2A33"],
    "foreground": "#1B2A33", "background": "#FFFFFF", "tableAccent": "#1F4E5F",
    "good": "#2F7A8C", "neutral": "#A9BCC6", "bad": "#E0A100",
    "maximum": "#1F4E5F", "center": "#A9BCC6", "minimum": "#E8EEF1",
}


def _altura_cabecalho(px: np.ndarray) -> int:
    coluna = px[:, px.shape[1] // 2, :3]
    for y, cor in enumerate(coluna):
        if cor.min() > 225:
            return y
    raise ValueError("cabeçalho não encontrado")


def _reconstruir_cabecalho(px: np.ndarray, hh: int) -> None:
    w = px.shape[1]
    cab = px[:hh, :, :3].astype(np.float64)
    fundo = cab[max(2, hh // 30), :, :]
    folga = np.maximum(255 - fundo, 1)
    alfa = np.clip(((cab - fundo) / folga).max(axis=2), 0, 1)
    t = np.linspace(0, 1, w)[:, None]
    novo_fundo = np.array(GRADIENTE[0]) * (1 - t) + np.array(GRADIENTE[1]) * t
    x0, x1 = int(FAIXA_TITULO[0] * w), int(FAIXA_TITULO[1] * w)
    alfa[:, x0:x1] = 0
    a = alfa[..., None]
    px[:hh, :, :3] = np.round(novo_fundo[None, :, :] * (1 - a) + 255 * a).astype(np.uint8)


def _escrever_titulos(img: Image.Image, hh: int, titulo: str) -> None:
    d = ImageDraw.Draw(img)
    x = int(FAIXA_TITULO[0] * img.width) + int(0.012 * img.width)
    f1 = ImageFont.truetype(FONTE, max(10, int(hh * 0.15)))
    f2 = ImageFont.truetype(FONTE_BOLD, max(14, int(hh * 0.27)))
    cx = x
    for ch in TITULO_PROGRAMA:
        d.text((cx, int(hh * 0.20)), ch, font=f1, fill=(214, 228, 234, 255))
        cx += d.textlength(ch, font=f1) + max(1, int(hh * 0.02))
    d.text((x, int(hh * 0.42)), titulo, font=f2, fill=(255, 255, 255, 255))


def gerar_fundo(caminho: Path, titulo_pagina: str) -> None:
    original = Image.open(caminho).convert("RGBA")
    px = np.array(original)
    hh = _altura_cabecalho(px)
    corpo = np.array(cores.recolorir_imagem(original))
    corpo[:hh] = px[:hh]
    _reconstruir_cabecalho(corpo, hh)
    img = Image.fromarray(corpo, "RGBA")
    _escrever_titulos(img, hh, titulo_pagina)
    if caminho.name == "Fundo_financeiro.png":
        recolorir_legenda(img, *LEGENDA_FINANCEIRO)
    for tipo, caixa, texto in TEXTOS_FUNDO.get(caminho.name, []):
        _reescrever(img, tipo, caixa, texto)
    img.save(caminho)


def _literal(valor: str) -> dict:
    return {"expr": {"Literal": {"Value": valor}}}


def liberar_periodo(visual: dict) -> bool:
    v = visual.get("visual", {})
    if v.get("visualType") != "slicer" or '"dCalendario"' not in json.dumps(v):
        return False
    for item in v.get("objects", {}).get("data", []):
        for chave in ("startDate", "endDate"):
            item.get("properties", {}).pop(chave, None)
    for item in v.get("objects", {}).get("general", []):
        item.get("properties", {}).pop("filter", None)
    return True


def limitar_eixo_evolucao(visual: dict) -> bool:
    v = visual.get("visual", {})
    if v.get("visualType") != "lineChart" or "Evo Criadas" not in json.dumps(v):
        return False
    medida = {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "Fato_Ideias"}},
                                   "Property": "Evo Eixo Max"}}}
    eixo = v.setdefault("objects", {}).setdefault("valueAxis", [{"properties": {}}])
    eixo[0].setdefault("properties", {})["end"] = medida
    eixo[0]["properties"]["start"] = _literal("0D")
    return True


def legenda_evolucao(visual: dict) -> bool:
    v = visual.get("visual", {})
    if v.get("visualType") != "lineChart" or "Evo Criadas" not in json.dumps(v):
        return False
    v.setdefault("objects", {})["legend"] = [{"properties": {
        "show": _literal("true"), "position": _literal("'TopLeft'"),
        "fontSize": _literal("8D"), "showTitle": _literal("false")}}]
    nomes = {"Evo Criadas": "Criadas", "Evo Implantadas": "Implantadas"}
    for papel in v["query"]["queryState"].values():
        for proj in papel.get("projections", []):
            prop = proj.get("field", {}).get("Measure", {}).get("Property")
            if prop in nomes:
                proj["displayName"] = nomes[prop]
    return True


def rotulos_sla_dentro(visual: dict) -> bool:
    v = visual.get("visual", {})
    if v.get("visualType") != "columnChart" or "Tempo Etapa Sel" not in json.dumps(v):
        return False
    props = v["objects"]["labels"][0]["properties"]
    props["labelPosition"] = _literal("'InsideEnd'")
    props["color"] = {"solid": {"color": _literal("'#FFFFFF'")}}
    for linha in v["objects"].get("y1AxisReferenceLine", []):
        if "dataLabelShow" in linha.get("properties", {}):
            linha["properties"]["dataLabelShow"] = _literal("false")
    return True


LARGURAS_COLUNAS = {
    "96b945cc4d714b8d17d9": {"Fato_Ideias.Ideia_Autor": "228D", "Fato_Ideias.Empresa_Sigla": "74D",
                             "Fato_Ideias.Tema_Curto": "132D", "Fato_Ideias.Data_Impl_Dia": "80D"},
}
ALTURAS = {"b8d04d7c02d728cf6af1": 432}
COLUNAS_LARGAS = {"d4f94d80d3c8ad14941f": 14}
CORES_PREV_INV_GANHO = {"Fato_Ideias.Prev Mil": "#1F4E5F", "Fato_Ideias.Inv Mil": "#A9BCC6",
                        "Fato_Ideias.Ganho Mil": "#1F7A5C"}
LEGENDA_FINANCEIRO = ((840, 322, 1110, 352), ("#1F4E5F", "#A9BCC6", "#1F7A5C"))


def recolorir_legenda(img: Image.Image, faixa, cores) -> int:
    k = img.width / 2000
    x0, y0, x1, y1 = (round(v * k) for v in faixa)
    px = img.load()
    saturado = {}
    for x in range(x0, x1):
        for y in range(y0, y1):
            r, g, b = px[x, y][:3]
            if max(r, g, b) - min(r, g, b) > 80:
                saturado.setdefault(x, []).append(y)
    grupos, atual = [], []
    for x in sorted(saturado):
        if atual and x - atual[-1] > 2:
            grupos.append(atual)
            atual = []
        atual.append(x)
    if atual:
        grupos.append(atual)
    grupos = [g for g in grupos if len(g) >= 8 * k]
    for grupo, cor in zip(grupos, cores, strict=False):
        rgb = tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))
        for x in grupo:
            for y in saturado[x]:
                px[x, y] = (*rgb, px[x, y][3]) if len(px[x, y]) == 4 else rgb
    return len(grupos)


LARGURA_MIN_EMPRESA = 74.0


def alargar_coluna_empresa(visual: dict) -> bool:
    larguras = visual.get("visual", {}).get("objects", {}).get("columnWidth", [])
    valor = lambda it: float(it["properties"]["value"]["expr"]["Literal"]["Value"].rstrip("D"))  # noqa: E731
    empresa = [it for it in larguras if it.get("selector", {}).get("metadata", "").endswith("Empresa_Sigla")]
    if not empresa or valor(empresa[0]) >= LARGURA_MIN_EMPRESA:
        return False
    falta = LARGURA_MIN_EMPRESA - valor(empresa[0])
    maior = max((it for it in larguras if it is not empresa[0]), key=valor)
    maior["properties"]["value"] = _literal(f"{valor(maior) - falta:.1f}D")
    empresa[0]["properties"]["value"] = _literal(f"{LARGURA_MIN_EMPRESA:.1f}D")
    return True


def ajustar_layout(arq: Path, visual: dict) -> bool:
    vid = arq.parent.name
    mudou = alargar_coluna_empresa(visual)
    for item in visual.get("visual", {}).get("objects", {}).get("columnWidth", []):
        nova = LARGURAS_COLUNAS.get(vid, {}).get(item.get("selector", {}).get("metadata"))
        if nova:
            item["properties"]["value"] = _literal(nova)
            mudou = True
    if vid in ALTURAS:
        visual["position"]["height"] = ALTURAS[vid]
        mudou = True
    for item in visual.get("visual", {}).get("objects", {}).get("dataPoint", []):
        cor = CORES_PREV_INV_GANHO.get(item.get("selector", {}).get("metadata"))
        if cor:
            item["properties"]["fill"] = {"solid": {"color": _literal(f"'{cor}'")}}
            mudou = True
    if vid in COLUNAS_LARGAS:
        for eixo in visual["visual"]["objects"].get("categoryAxis", []):
            eixo["properties"]["innerPadding"] = _literal(f"{COLUNAS_LARGAS[vid]}L")
        mudou = True
    return mudou


def ajustar_relatorio(rep: Path) -> None:
    for arq in (rep / "definition" / "pages").rglob("visual.json"):
        d = json.loads(arq.read_text(encoding="utf-8-sig"))
        mudou = [liberar_periodo(d), limitar_eixo_evolucao(d), legenda_evolucao(d),
                 rotulos_sla_dentro(d), ajustar_layout(arq, d)]
        if any(mudou):
            arq.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def aplicar(raiz: Path) -> None:
    rep = raiz / f"{NOME}.Report"
    sm = raiz / f"{NOME}.SemanticModel" / "definition" / "tables"
    for p in list((rep / "definition").rglob("*.json")) + list(sm.glob("*.tmdl")):
        s = p.read_text(encoding="utf-8-sig")
        novo = cores.remapear_interpolacao_dax(cores.remapear_texto(s)).replace(
            "'SLA 60 d'", f"'SLA geral {metas.SLA_GERAL_DIAS} d'").replace(
            '"60D"', f'"{metas.SLA_GERAL_DIAS}D"')
        if novo != s:
            p.write_text(novo, encoding="utf-8")

    ajustar_relatorio(rep)

    recursos = rep / "StaticResources" / "RegisteredResources"
    for arquivo, titulo in PAGINAS.items():
        gerar_fundo(recursos / arquivo, titulo)

    (recursos / "TemaPainelIdeias.json").write_text(json.dumps(TEMA, indent=2), encoding="utf-8")
    report_json = rep / "definition" / "report.json"
    r = json.loads(report_json.read_text(encoding="utf-8-sig"))
    base = r["themeCollection"]["baseTheme"]
    r["themeCollection"]["customTheme"] = {"name": "TemaPainelIdeias.json",
                                           "reportVersionAtImport": base["reportVersionAtImport"],
                                           "type": "RegisteredResources"}
    for pacote in r.get("resourcePackages", []):
        if pacote.get("name") == "RegisteredResources":
            itens = pacote.setdefault("items", [])
            if not any(i.get("name") == "TemaPainelIdeias.json" for i in itens):
                itens.append({"name": "TemaPainelIdeias.json", "path": "TemaPainelIdeias.json",
                              "type": "CustomTheme"})
    report_json.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    aplicar(Path(__file__).resolve().parents[1] / "powerbi")
    print("OK: cores, fundos e tema aplicados")
