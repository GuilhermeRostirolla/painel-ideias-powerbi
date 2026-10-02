import io
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer, SqlLexer, TextLexer

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "saida" / "linkedin"
FONTE_CODIGO = "Consolas"
FONTE_TITULO = r"C:\Windows\Fonts\segoeui.ttf"
FUNDO = ((0x17, 0x3E, 0x4C), (0x2F, 0x7A, 0x8C))
ESTILO = "one-dark"

TRECHOS = [
    ("01_python_fluxo.png", "gerador/fluxo.py", "def simular_ideia", 17,
     "Python · simulação do ciclo de vida de cada ideia (máquina de estados)"),
    ("02_python_parametros.png", "gerador/config.py", "TRANSICOES_BASE", 11,
     "Python · probabilidades de transição entre etapas"),
    ("03_python_valores.png", "gerador/valores.py", "def gerar_valores", 19,
     "Python · valores com perfil financeiro próprio por empresa"),
    ("04_python_titulos.png", "gerador/catalogos.py", "_DOMINIOS = (", 17,
     "Python · títulos coerentes: cada atividade só nas áreas onde acontece"),
    ("05_python_validacao.png", "gerador/validar.py", "def validar", 19,
     "Python · regras que bloqueiam a carga se algo estiver incoerente"),
    ("06_sql_fato.png", "sql/01_schema.sql", "CREATE TABLE dw.fato_ideia", 42,
     "SQL Server · tabela fato com chaves, constraints nomeadas e regras CHECK"),
    ("07_sql_indices.png", "sql/01_schema.sql", "CREATE INDEX", 15,
     "SQL Server · índice em todas as chaves estrangeiras"),
    ("08_sql_views.png", "sql/03_views_compat.sql", "CREATE VIEW bi.vw_Dim_SLA_Ideias", 23,
     "SQL Server · views do schema bi consumidas pelo Power BI"),
    ("09_sql_dimensoes.png", "sql/01_schema.sql", "CREATE TABLE dw.dim_unidade", 21,
     "SQL Server · dimensões do star schema (schema dw)"),
]


def _trecho(caminho: str, inicio: str, n: int) -> tuple[str, int]:
    linhas = (RAIZ / caminho).read_text(encoding="utf-8").splitlines()
    i = next(k for k, linha in enumerate(linhas) if linha.startswith(inicio))
    return "\n".join(linhas[i:i + n]), i + 1


def _render_codigo(codigo: str, lexer, primeira_linha: int | None) -> Image.Image:
    fmt = ImageFormatter(style=ESTILO, font_name=FONTE_CODIGO, font_size=22,
                         line_numbers=primeira_linha is not None,
                         line_number_start=primeira_linha or 1, line_number_bg="#21252b",
                         line_number_fg="#5c6370", line_pad=6, image_pad=24)
    return Image.open(io.BytesIO(highlight(codigo, lexer, fmt))).convert("RGB")


def _moldura(codigo: Image.Image, titulo: str, legenda: str) -> Image.Image:
    barra, margem, rodape = 46, 70, 70
    f_legenda = ImageFont.truetype(FONTE_TITULO, 26)
    largura_legenda = round(ImageDraw.Draw(codigo).textlength(legenda, font=f_legenda))
    if largura_legenda > codigo.width:
        base = Image.new("RGB", (largura_legenda, codigo.height), "#282c34")
        base.paste(codigo, (0, 0))
        codigo = base
    w = codigo.width + 2 * margem
    h = codigo.height + barra + 2 * margem + rodape
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / max(1, w - 1)
        d.line([(x, 0), (x, h)], fill=tuple(round(a + (b - a) * t) for a, b in zip(*FUNDO, strict=True)))
    x0, y0 = margem, margem
    x1, y1 = x0 + codigo.width, y0 + barra + codigo.height
    d.rounded_rectangle((x0 + 6, y0 + 10, x1 + 6, y1 + 10), radius=16, fill=(10, 30, 38))
    d.rounded_rectangle((x0, y0, x1, y1), radius=16, fill="#21252b")
    for i, cor in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        cx = x0 + 24 + i * 24
        d.ellipse((cx - 7, y0 + barra // 2 - 7, cx + 7, y0 + barra // 2 + 7), fill=cor)
    f_titulo = ImageFont.truetype(FONTE_TITULO, 20)
    d.text(((x0 + x1) / 2, y0 + barra / 2), titulo, font=f_titulo, fill="#abb2bf", anchor="mm")
    img.paste(codigo, (x0, y0 + barra))
    d.text((x0, y1 + rodape / 2 + 20), legenda, font=f_legenda, fill="#E8EEF1", anchor="lm")
    return img


def _execucao() -> str:
    sys.path.insert(0, str(RAIZ))
    from sqlalchemy import text

    from gerador.banco import criar_engine
    with criar_engine("localhost", "IdeiasDemo").connect() as c:
        semente, data_ref = c.execute(text("SELECT semente, data_referencia FROM dw.meta_carga")).one()
    args = ["--semente", str(semente), "--data-referencia", data_ref.isoformat()]
    r = subprocess.run([sys.executable, "-m", "gerador.main", *args], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8", check=True)
    return "> python -m gerador.main " + " ".join(args) + "\n" + r.stdout.strip()


CONSULTA = """\
SELECT   u.sigla                                              AS empresa,
         COUNT(*)                                             AS ideias,
         SUM(CASE WHEN f.data_implantacao IS NOT NULL THEN 1 ELSE 0 END) AS implantadas,
         CAST(SUM(f.investimento_previsto) / 1e6 AS DECIMAL(6, 1)) AS previsto_mi,
         CAST(SUM(f.investimento_real)     / 1e6 AS DECIMAL(6, 1)) AS investido_mi,
         CAST(SUM(f.ganho_previsto_12m)    / 1e6 AS DECIMAL(6, 1)) AS ganho_mi
FROM     dw.fato_ideia  AS f
JOIN     dw.dim_unidade AS u ON u.id_unidade = f.id_unidade
GROUP BY u.sigla
ORDER BY ganho_mi DESC;"""


def _consulta() -> str:
    sys.path.insert(0, str(RAIZ))
    from sqlalchemy import text

    from gerador.banco import criar_engine
    with criar_engine("localhost", "IdeiasDemo").connect() as c:
        r = c.execute(text(CONSULTA))
        colunas, linhas = list(r.keys()), [[str(v) for v in linha] for linha in r]
    larguras = [max(len(x) for x in [col, *(linha[i] for linha in linhas)]) for i, col in enumerate(colunas)]

    def fmt(valores: list[str]) -> str:
        return "  ".join(v.ljust(w) if i == 0 else v.rjust(w)
                         for i, (v, w) in enumerate(zip(valores, larguras, strict=True)))
    tabela = [fmt(colunas), "  ".join("-" * w for w in larguras), *(fmt(linha) for linha in linhas)]
    return CONSULTA + "\n\n" + "\n".join(tabela) + f"\n\n({len(linhas)} linhas)"


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    for arquivo, caminho, inicio, n, legenda in TRECHOS:
        codigo, linha = _trecho(caminho, inicio, n)
        lexer = SqlLexer() if caminho.endswith(".sql") else PythonLexer()
        _moldura(_render_codigo(codigo, lexer, linha), caminho, legenda).save(SAIDA / arquivo)
        print(SAIDA / arquivo)
    terminal = _render_codigo(_execucao(), TextLexer(), None)
    _moldura(terminal, "Terminal", "Geração + validação + carga no SQL Server em uma execução").save(
        SAIDA / "10_terminal.png")
    print(SAIDA / "10_terminal.png")
    consulta = _render_codigo(_consulta(), SqlLexer(), None)
    legenda = "SQL Server · consulta no star schema: resultado por empresa"
    _moldura(consulta, "SQL Server · IdeiasDemo", legenda).save(SAIDA / "18_sql_consulta.png")
    print(SAIDA / "18_sql_consulta.png")


if __name__ == "__main__":
    main()
