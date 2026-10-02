import json
import shutil
import sys
from pathlib import Path

NOME = "PainelIdeias"
IGNORAR = shutil.ignore_patterns(".pbi", "cultures", "roles", "cache.abf")


def _ler(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8-sig"))


def _gravar(p: Path, d: dict) -> None:
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def copiar(origem_pbip: Path, destino: Path) -> Path:
    base = origem_pbip.with_suffix("")
    rep_src = Path(f"{base}.Report")
    sm_src = Path(f"{base}.SemanticModel")
    rep_dst = destino / f"{NOME}.Report"
    sm_dst = destino / f"{NOME}.SemanticModel"
    if rep_dst.exists() or sm_dst.exists():
        raise FileExistsError(f"{destino} já contém o projeto; apague manualmente para recopiar")
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copytree(rep_src, rep_dst, ignore=IGNORAR)
    shutil.copytree(sm_src, sm_dst, ignore=IGNORAR)

    pbir = rep_dst / "definition.pbir"
    d = _ler(pbir)
    d["datasetReference"]["byPath"]["path"] = f"../{NOME}.SemanticModel"
    _gravar(pbir, d)

    pbip = _ler(origem_pbip)
    for art in pbip["artifacts"]:
        art["report"]["path"] = f"{NOME}.Report"
    novo = destino / f"{NOME}.pbip"
    _gravar(novo, pbip)

    for plat in (rep_dst / ".platform", sm_dst / ".platform"):
        if plat.exists():
            d = _ler(plat)
            d["metadata"]["displayName"] = NOME
            _gravar(plat, d)
    return novo


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("uso: python tools/copiar_pbip.py <caminho do .pbip original>")
    print(copiar(Path(sys.argv[1]), Path(__file__).resolve().parents[1] / "powerbi"))
