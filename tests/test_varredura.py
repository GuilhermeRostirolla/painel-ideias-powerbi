import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import varredura  # noqa: E402

from gerador.blocklist import hash_texto  # noqa: E402


def test_detecta_marca_e_nome(tmp_path: Path):
    (tmp_path / "a.json").write_text('{"t": "Relatório da Exemplar"}', encoding="utf-8")
    (tmp_path / "b.py").write_text("autor = 'Ana Maria Teste'", encoding="utf-8")
    (tmp_path / "c.py").write_text("x = 'nada aqui'", encoding="utf-8")
    achados = varredura.varrer(tmp_path, frozenset({hash_texto("exemplar")}),
                               frozenset({hash_texto("ana maria teste")}))
    assert sorted(achados) == ["a.json:1", "b.py:1"]


def test_nome_de_uma_palavra_nao_conta(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 'estoque'", encoding="utf-8")
    assert varredura.varrer(tmp_path, frozenset(), frozenset({hash_texto("estoque")})) == []


def test_ignora_pastas_e_permitidos(tmp_path: Path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "x.py").write_text("exemplar", encoding="utf-8")
    (tmp_path / "c.tmdl").write_text("column 'Parâmetro Pedido'", encoding="utf-8")
    hashes = frozenset({hash_texto("exemplar"), hash_texto("pedido")})
    assert varredura.varrer(tmp_path, hashes) == []
