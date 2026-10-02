import colorsys
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cores  # noqa: E402


def _h(hexs):
    r, g, b = (int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def test_vinho_vira_petroleo():
    assert 185 <= _h(cores.remapear_hex("#7A1F3D")) <= 210


def test_vermelho_vivo_vira_ambar():
    assert 35 <= _h(cores.remapear_hex("#E0192E")) <= 50


def test_rosa_claro_vira_azul_claro():
    assert 185 <= _h(cores.remapear_hex("#EAD0D8")) <= 210


def test_neutros_e_verdes_intocados():
    for c in ("#FFFFFF", "#000000", "#808080", "#2E8B57", "#F5F5F5"):
        assert cores.remapear_hex(c) == c


def test_remapear_texto_preserva_caixa():
    out = cores.remapear_texto('{"color":"#7a1f3d","x":"#FFFFFF"}')
    assert "#7a1f3d" not in out and '"#FFFFFF"' in out
    assert out.split('"color":"')[1][:7] == out.split('"color":"')[1][:7].lower()


def test_interpolacao_dax_vinho_vira_petroleo():
    dax = ("VAR __r = ROUND ( 255 - __a * 124, 0 ) VAR __g = ROUND ( 255 - __a * 216, 0 ) "
           "VAR __b = ROUND ( 255 - __a * 188, 0 )")
    out = cores.remapear_interpolacao_dax(dax)
    import re
    dr, dg, db = (int(x) for x in re.findall(r"__a \* (\d+)", out))
    alvo = f"#{255 - dr:02X}{255 - dg:02X}{255 - db:02X}"
    assert 185 <= _h(alvo) <= 210
    assert cores.remapear_interpolacao_dax(out) == out


def test_recolorir_imagem_preserva_alfa():
    out = cores.recolorir_imagem(Image.new("RGBA", (4, 4), (122, 31, 61, 128)))
    assert out.mode == "RGBA" and out.getpixel((0, 0))[3] == 128
    r, g, b, _ = out.getpixel((0, 0))
    assert b > r
