import colorsys
import re

import numpy as np
from PIL import Image

H_PETROLEO = 197 / 360
H_AMBAR = 43 / 360
S_MIN = 0.03


def _eh_avermelhado(h: float, s: float) -> bool:
    return s >= S_MIN and (h <= 25 / 360 or h >= 300 / 360)


def _novo_h(s: float, v: float) -> float:
    return H_AMBAR if (v >= 0.55 and s >= 0.6) else H_PETROLEO


def remapear_rgb(r: int, g: int, b: int) -> tuple[int, int, int]:
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if not _eh_avermelhado(h, s):
        return r, g, b
    nr, ng, nb = colorsys.hsv_to_rgb(_novo_h(s, v), s, v)
    return round(nr * 255), round(ng * 255), round(nb * 255)


def remapear_hex(hex6: str) -> str:
    r, g, b = (int(hex6[i:i + 2], 16) for i in (1, 3, 5))
    nr, ng, nb = remapear_rgb(r, g, b)
    if (nr, ng, nb) == (r, g, b):
        return hex6
    saida = f"#{nr:02X}{ng:02X}{nb:02X}"
    return saida.lower() if hex6[1:].islower() else saida


def remapear_texto(texto: str) -> str:
    return re.sub(r"#[0-9A-Fa-f]{6}(?![0-9A-Fa-f])", lambda m: remapear_hex(m.group(0)), texto)


_INTERP_DAX = re.compile(
    r"(255 - (__\w+) \* )(\d+)(, 0 \) VAR __g = ROUND \( 255 - \2 \* )(\d+)"
    r"(, 0 \) VAR __b = ROUND \( 255 - \2 \* )(\d+)")


def remapear_interpolacao_dax(texto: str) -> str:
    def trocar(m: re.Match) -> str:
        alvo = tuple(255 - int(m.group(i)) for i in (3, 5, 7))
        r, g, b = (255 - c for c in remapear_rgb(*alvo))
        return f"{m.group(1)}{r}{m.group(4)}{g}{m.group(6)}{b}"
    return _INTERP_DAX.sub(trocar, texto)


def recolorir_imagem(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    alfa = rgba.getchannel("A")
    hsv = np.array(rgba.convert("RGB").convert("HSV")).astype(np.int32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mask = (s >= round(S_MIN * 255)) & ((h <= round(25 / 360 * 255)) | (h >= round(300 / 360 * 255)))
    ambar = mask & (v >= round(0.55 * 255)) & (s >= round(0.6 * 255))
    h[mask] = round(H_PETROLEO * 255)
    h[ambar] = round(H_AMBAR * 255)
    out = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB").convert("RGBA")
    out.putalpha(alfa)
    return out
