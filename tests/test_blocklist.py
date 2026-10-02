from pathlib import Path

import pytest

from gerador.blocklist import bloqueado, carregar, hash_texto, normalizar


def test_normalizar_remove_acento_caixa_espacos():
    assert normalizar("  João   da SILVA ") == "joao da silva"


def test_hash_ignora_acento_e_caixa():
    assert hash_texto("José Conceição") == hash_texto("jose  conceicao")


def test_carregar_e_bloqueado(tmp_path: Path):
    arq = tmp_path / "b.sha256"
    arq.write_text(hash_texto("Maria Souza") + "\n\n")
    bl = carregar(arq)
    assert bloqueado("MARIA SOUZA", bl)
    assert not bloqueado("Maria Souza Lima", bl)


def test_carregar_ausente_da_erro_claro(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="extrair_referencias"):
        carregar(tmp_path / "nao_existe")
