import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gerador.blocklist import hash_texto, normalizar  # noqa: E402


def main() -> None:
    destino = Path(sys.argv[1])
    min_palavras = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == "--min-palavras" else 1
    sys.stdin.reconfigure(encoding="utf-8")
    textos = {normalizar(linha) for linha in sys.stdin.read().splitlines()}
    textos = {t for t in textos if t and len(t.split()) >= min_palavras}
    destino.parent.mkdir(parents=True, exist_ok=True)
    existentes = set(destino.read_text().split()) if destino.exists() else set()
    novos = existentes | {hash_texto(t) for t in textos}
    destino.write_text("\n".join(sorted(novos)) + "\n")
    print(f"{len(novos)} hashes em {destino}")


if __name__ == "__main__":
    main()
