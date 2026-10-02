import collections
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "powerbi"
SM = RAIZ / "PainelIdeias.SemanticModel" / "definition" / "tables"
REP = RAIZ / "PainelIdeias.Report" / "definition"

_OBJ = re.compile(
    r"^\t(measure|column) ('[^']+'|[^\n=]+?)\s*=\s*(.*?)"
    r"(?=^\t\t(?:dataType|formatString|lineageTag|displayFolder|isHidden|summarizeBy|annotation)"
    r"|^\t(?:measure|column|partition|hierarchy|annotation)|\Z)", re.M | re.S)
_TAB_CALC = re.compile(r"^\tpartition [^\n]*= calculated\n.*?source =(.*?)(?=^\t[^\t]|\Z)", re.M | re.S)
_REF_TAB = re.compile(r"'?([A-Za-zÀ-ú_][\w À-ú]*?)'?\[([^\]]+)\]")
_REF_SOLTA = re.compile(r"(?<![\w'\]])\[([^\]]+)\]")


def carregar(sm: Path = SM) -> tuple[dict, dict, dict]:
    objs, calc, tabelas = {}, {}, {}
    for arq in sm.glob("*.tmdl"):
        s = arq.read_text(encoding="utf-8-sig")
        t = s.splitlines()[0][6:].strip().strip("'")
        tabelas[t] = arq
        for m in _OBJ.finditer(s):
            objs[(t, m.group(2).strip().strip("'"))] = (m.group(1), m.group(3))
        p = _TAB_CALC.search(s)
        if p:
            calc[t] = p.group(1)
    return objs, calc, tabelas


def usados(objs: dict, calc: dict, rep_dir: Path = REP) -> set:
    rep = "".join(p.read_text(encoding="utf-8") for p in rep_dir.rglob("*.json"))
    raizes = set(re.findall(r'"Entity":\s*"([^"]+)"\s*\}\s*\}\s*,\s*"Property":\s*"([^"]+)"', rep))
    raizes |= {(t, "*") for t in re.findall(r'"Entity":\s*"([^"]+)"', rep)}
    return fechamento(raizes, objs, calc)


def fechamento(raizes: set, objs: dict, calc: dict) -> set:
    medidas = {n: t for (t, n), (k, _) in objs.items() if k == "measure"}

    def deps(expr: str) -> set:
        out = {(t.strip(), c) for t, c in _REF_TAB.findall(expr)}
        out |= {(medidas[c], c) for c in _REF_SOLTA.findall(expr) if c in medidas}
        return out

    vistos, fila = set(), list(raizes)
    while fila:
        x = fila.pop()
        if x in vistos:
            continue
        vistos.add(x)
        if x in objs:
            fila.extend(deps(objs[x][1]))
        if x[0] in calc and (x[0], "__tabela__") not in vistos:
            vistos.add((x[0], "__tabela__"))
            fila.extend(deps(calc[x[0]]))
    return vistos


def main() -> None:
    objs, calc, tabelas = carregar()
    vistos = usados(objs, calc)
    tab_usadas = {t for t, _ in vistos}
    print("Tabelas sem uso (nenhum visual chega nelas):")
    for t in sorted(tabelas):
        if t not in tab_usadas:
            print("   ", t)
    sem_uso = sorted(n for (t, n), (k, _) in objs.items() if k == "measure" and (t, n) not in vistos)
    print(f"\nMedidas sem uso: {len(sem_uso)} de "
          f"{sum(1 for k, _ in objs.values() if k == 'measure')}")
    contagem = collections.Counter(t for (t, n), (k, _) in objs.items()
                                   if k == "measure" and (t, n) not in vistos)
    print("   por tabela:", dict(contagem))


if __name__ == "__main__":
    main()
