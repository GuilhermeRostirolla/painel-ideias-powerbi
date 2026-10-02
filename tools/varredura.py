import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gerador.blocklist import (  # noqa: E402
    CAMINHO_BLOCKLIST,
    CAMINHO_PROIBIDOS,
    carregar,
    hash_texto,
    normalizar,
)

IGNORAR = {".venv", ".git", "__pycache__", ".pytest_cache", "superpowers", "saida"}
EXTENSOES = {".py", ".sql", ".json", ".tmdl", ".pbir", ".pbism", ".pbip", ".md", ".ps1",
             ".txt", ".ini", ".platform", ""}
PERMITIDOS = frozenset(hash_texto(t) for t in ("pedido", "em etapas anteriores"))


def _arquivos(raiz: Path):
    for p in raiz.rglob("*"):
        if p.is_file() and not IGNORAR & set(p.relative_to(raiz).parts) and p.suffix in EXTENSOES:
            yield p


def _linha_tem(palavras: list[str], proibidos: frozenset[str], nomes: frozenset[str],
               max_n: int) -> bool:
    for n in range(1, max_n + 1):
        for k in range(len(palavras) - n + 1):
            h = hash_texto(" ".join(palavras[k:k + n]))
            if h in PERMITIDOS:
                continue
            if h in proibidos or (n >= 2 and h in nomes):
                return True
    return False


def varrer(raiz: Path, proibidos: frozenset[str], nomes: frozenset[str] = frozenset(),
           max_n: int = 6) -> list[str]:
    achados = []
    for p in _arquivos(raiz):
        try:
            texto = p.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        for i, linha in enumerate(texto.splitlines(), 1):
            if _linha_tem(re.findall(r"[\w&]+", normalizar(linha)), proibidos, nomes, max_n):
                achados.append(f"{p.relative_to(raiz)}:{i}")
    return achados


if __name__ == "__main__":
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    r = varrer(raiz, carregar(CAMINHO_PROIBIDOS), carregar(CAMINHO_BLOCKLIST))
    if r:
        print("TERMOS PROIBIDOS ENCONTRADOS (arquivo:linha):\n  " + "\n  ".join(r))
        sys.exit(1)
    print("OK: nenhum termo proibido")
