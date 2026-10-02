from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "saida" / "linkedin"
SAIDA = ORIGEM / "carrossel"
W, H, M = 1080, 1350, 56
FUNDO = ((0x12, 0x33, 0x40), (0x23, 0x63, 0x73))
AMBAR = (0xE0, 0xA1, 0x00)
BRANCO, CLARO, SUAVE = (255, 255, 255), (0xD6, 0xE4, 0xEA), (0x9F, 0xBC, 0xC7)
FONTES = r"C:\Windows\Fonts"


def _f(nome: str, tam: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(f"{FONTES}\\{nome}", tam)


def _fundo() -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(*FUNDO, strict=True)))
    return img


def _quebrar(d: ImageDraw.ImageDraw, texto: str, fonte, largura: int) -> list[str]:
    linhas, atual = [], ""
    for p in texto.split():
        teste = f"{atual} {p}".strip()
        if d.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    return linhas + [atual]


def _texto(d, xy, texto, fonte, cor, largura, entre=1.25) -> int:
    x, y = xy
    for linha in _quebrar(d, texto, fonte, largura):
        d.text((x, y), linha, font=fonte, fill=cor)
        y += round(fonte.size * entre)
    return y


def _colar_print(img: Image.Image, foto: Image.Image, y: int, largura: int = W - 2 * M) -> int:
    foto = foto.resize((largura, round(foto.height * largura / foto.width)), Image.LANCZOS)
    mascara = Image.new("L", foto.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, *foto.size), radius=18, fill=255)
    sombra = Image.new("RGBA", (foto.width + 60, foto.height + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((30, 40, foto.width + 30, foto.height + 40), radius=18,
                                             fill=(0, 0, 0, 110))
    sombra = sombra.filter(ImageFilter.GaussianBlur(14))
    img.paste(sombra, ((W - foto.width) // 2 - 30, y - 30), sombra)
    img.paste(foto, ((W - foto.width) // 2, y), mascara)
    return y + foto.height


def _moldura(n: int, total: int, rotulo: str, titulo: str, subtitulo: str) -> tuple[Image.Image, int]:
    img = _fundo()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((M, 70, M + 64, 76), radius=3, fill=AMBAR)
    d.text((M, 92), rotulo.upper(), font=_f("seguisb.ttf", 24), fill=SUAVE)
    y = _texto(d, (M, 140), titulo, _f("segoeuib.ttf", 62), BRANCO, W - 2 * M, 1.15)
    y = _texto(d, (M, y + 16), subtitulo, _f("segoeui.ttf", 32), CLARO, W - 2 * M, 1.35)
    d.text((M, H - 70), "Painel de Ideias  ·  dados 100% fictícios", font=_f("segoeui.ttf", 24), fill=SUAVE)
    d.text((W - M, H - 70), f"{n} / {total}", font=_f("seguisb.ttf", 24), fill=SUAVE, anchor="ra")
    return img, y + 50


def _destaque(img: Image.Image, y: int, texto: str) -> None:
    d = ImageDraw.Draw(img)
    f = _f("seguisb.ttf", 30)
    linhas = _quebrar(d, texto, f, W - 2 * M - 70)
    h = 36 + len(linhas) * 42
    d.rounded_rectangle((M, y, W - M, y + h), radius=16, fill=(0x0E, 0x2A, 0x35))
    d.rounded_rectangle((M, y, M + 8, y + h), radius=4, fill=AMBAR)
    for i, linha in enumerate(linhas):
        d.text((M + 36, y + 18 + i * 42), linha, font=f, fill=BRANCO)


def _slide_print(n, total, rotulo, titulo, subtitulo, foto: Image.Image, destaque: str) -> Image.Image:
    img, y = _moldura(n, total, rotulo, titulo, subtitulo)
    d = ImageDraw.Draw(img)
    alt_foto = round(foto.height * (W - 2 * M) / foto.width)
    alt_dest = 36 + len(_quebrar(d, destaque, _f("seguisb.ttf", 30), W - 2 * M - 70)) * 42
    sobra = (H - 110) - (y + alt_foto + 48 + alt_dest)
    fim = _colar_print(img, foto, y + max(0, sobra // 2))
    _destaque(img, fim + 48, destaque)
    return img


def _slide_arquitetura(n: int, total: int) -> Image.Image:
    img, y = _moldura(n, total, "Como foi feito", "Do zero, de ponta a ponta",
                      "Os dados originais são sensíveis. Então recriei tudo com dados fictícios, "
                      "do simulador ao painel.")
    d = ImageDraw.Draw(img)
    etapas = [("Python", "Simulador que imita o programa real: prazos, retrabalho, reprovações "
                         "e retorno por empresa"),
              ("SQL Server", "Star schema com chaves, regras de integridade e views para o Power BI"),
              ("Power BI", "6 páginas, DAX, Power Query e segurança por empresa (RLS)")]
    ft, fd = _f("segoeuib.ttf", 40), _f("segoeui.ttf", 28)
    for i, (nome, desc) in enumerate(etapas):
        topo = y + i * 230
        d.rounded_rectangle((M, topo, W - M, topo + 170), radius=20, fill=(0x0E, 0x2A, 0x35))
        d.ellipse((M + 30, topo + 30, M + 90, topo + 90), fill=AMBAR)
        d.text((M + 60, topo + 60), str(i + 1), font=_f("segoeuib.ttf", 32), fill=FUNDO[0], anchor="mm")
        d.text((M + 120, topo + 30), nome, font=ft, fill=BRANCO)
        _texto(d, (M + 120, topo + 86), desc, fd, CLARO, W - 2 * M - 150, 1.3)
        if i < len(etapas) - 1:
            cx = W // 2
            d.polygon([(cx - 18, topo + 182), (cx + 18, topo + 182), (cx, topo + 214)], fill=AMBAR)
    _destaque(img, y + 3 * 230 + 10,
              "Código, modelo de dados e decisões do projeto no GitHub: link nos comentários")
    return img


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    rls = Image.open(ORIGEM / "janelas" / "pbi_9_rls_litoral.png").crop((60, 138, 1500, 937))
    total = 6
    slides = [
        _slide_print(1, total, "Projeto · Power BI + SQL Server + Python", "Ideia boa nunca faltou.",
                     "O desafio era fazer cada uma delas ser vista, do chão de fábrica até a alta gestão.",
                     Image.open(ORIGEM / "11_dash_visao_geral.png"),
                     "Painel de gestão de um programa de ideias e melhoria contínua"),
        _slide_print(2, total, "SLA & Fluxo", "Onde as ideias travam?",
                     "O tempo de cada etapa contra o SLA e as ideias paradas há mais de 60 dias.",
                     Image.open(ORIGEM / "12_dash_sla_fluxo.png"),
                     "Avaliação levando 18 dias, acima do SLA de 15: o primeiro retorno já chega atrasado"),
        _slide_print(3, total, "Financeiro", "O programa se paga?",
                     "Previsto, investido e ganho estimado em 12 meses, por empresa e por status.",
                     Image.open(ORIGEM / "14_dash_financeiro.png"),
                     "R$ 7,8 mi investidos para R$ 33,4 mi de ganho estimado"),
        _slide_print(4, total, "Colaboradores", "Quem está participando?",
                     "Engajamento de cada empresa contra a meta e quem mais contribui com ideias.",
                     Image.open(ORIGEM / "15_dash_colaboradores.png"),
                     "39% de engajamento contra meta de 50%: só 1 de 6 empresas bate a meta"),
        _slide_print(5, total, "Segurança", "Cada empresa vê só os seus dados",
                     "Segurança por linha (RLS) com um papel por empresa. "
                     "Aqui, o painel visto como a Litoral.",
                     rls, "196 ideias da Litoral, de 872 no total do programa"),
        _slide_arquitetura(6, total),
    ]
    for i, s in enumerate(slides, 1):
        s.save(SAIDA / f"slide_{i}.png")
    slides[0].save(SAIDA / "carrossel_painel_ideias.pdf", save_all=True, append_images=slides[1:],
                   resolution=150)
    print(SAIDA)


if __name__ == "__main__":
    main()
