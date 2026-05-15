import sys
from pathlib import Path

import scripts.avaliar_revisao as avaliar


def test_compare_without_pdfs_does_not_break(tmp_path, monkeypatch):
    monkeypatch.setattr(avaliar, "INPUT_DIR", tmp_path / "entrada")
    monkeypatch.setattr(avaliar, "OUTPUT_DIR", tmp_path / "saida")
    monkeypatch.setattr(avaliar, "REPORT_DIR", tmp_path / "relatorios")
    monkeypatch.setattr(sys, "argv", ["avaliar_revisao.py", "--compare"])
    code = avaliar.main()
    assert code == 0
    assert list((tmp_path / "relatorios").glob("comparativo_*.json"))
