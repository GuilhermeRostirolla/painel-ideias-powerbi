import hashlib
import os
import unicodedata
from pathlib import Path

PASTA_LOCAL = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "PainelIdeias"
CAMINHO_BLOCKLIST = PASTA_LOCAL / "blocklist.sha256"
CAMINHO_PROIBIDOS = PASTA_LOCAL / "proibidos.sha256"


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def hash_texto(texto: str) -> str:
    return hashlib.sha256(normalizar(texto).encode()).hexdigest()


def carregar(caminho: Path = CAMINHO_BLOCKLIST) -> frozenset[str]:
    if not caminho.exists():
        raise FileNotFoundError(
            f"arquivo de hashes ausente: {caminho}. Rode tools/extrair_referencias.ps1"
        )
    return frozenset(linha.strip() for linha in caminho.read_text().splitlines() if linha.strip())


def bloqueado(texto: str, bloqueio: frozenset[str]) -> bool:
    return hash_texto(texto) in bloqueio
