import json
import sys
from collections import Counter
from pathlib import Path

import scripts.avaliar_revisao as avaliar
from scripts.criar_manifesto_base import build_manifest


def test_base01_path_constants():
    avaliar.configure_base("base_01")
    assert avaliar.INPUT_DIR.as_posix().endswith("tests/documentos_referencia/base_01/entrada")
    assert avaliar.OUTPUT_DIR.as_posix().endswith("tests/documentos_referencia/base_01/saida")
    assert avaliar.REPORT_DIR.as_posix().endswith("tests/documentos_referencia/base_01/relatorios_avaliacao")
    assert avaliar.CHECKLIST_DIR.as_posix().endswith("tests/documentos_referencia/base_01/checklist_humano")
    avaliar.configure_base(None)


def test_manifest_without_documents_does_not_break(tmp_path):
    manifest = build_manifest(tmp_path / "entrada")
    assert manifest["total_arquivos"] == 0
    assert manifest["arquivos"] == []


def test_avaliar_base01_without_files_does_not_break(tmp_path, monkeypatch):
    base = tmp_path / "base_01"
    monkeypatch.setattr(avaliar, "REFERENCE_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["avaliar_revisao.py", "--base", "base_01", "--mode", "mock"])
    code = avaliar.main()
    assert code == 0
    assert (base / "entrada").exists()
    assert (base / "saida").exists()
    assert (base / "relatorios_avaliacao").exists()


def test_api_summary_without_jsons_does_not_break(tmp_path, monkeypatch):
    monkeypatch.setattr(avaliar, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(avaliar, "CURRENT_BASE", "base_01")
    path = avaliar.write_api_summary()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_documentos"] == 0
    assert data["total_apontamentos"] == 0


def test_risk_score_and_level_rules():
    assert avaliar.calculate_risk(Counter(), 0)["risk_level"] == "SEM_APONTAMENTOS"
    assert avaliar.calculate_risk(Counter({"BAIXA": 2}), 2)["risk_level"] == "BAIXO"
    assert avaliar.calculate_risk(Counter({"MEDIA": 1}), 1)["risk_level"] == "MEDIO"
    assert avaliar.calculate_risk(Counter({"ALTA": 1}), 1)["risk_level"] == "ALTO"
    assert avaliar.calculate_risk(Counter({"CRITICA": 1}), 1)["risk_level"] == "CRITICO"
    assert avaliar.calculate_risk(Counter({"ALTA": 6}), 6)["risk_level"] == "CRITICO"


def test_checklist_model_exists_with_expected_columns():
    path = Path("tests/documentos_referencia/base_01/checklist_humano/MODELO_CHECKLIST_REVISAO.csv")
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == avaliar.CHECKLIST_COLUMNS


def test_gitignore_covers_base01_sensitive_patterns():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "tests/documentos_referencia/base_01/entrada/**/*.pdf" in gitignore
    assert "tests/documentos_referencia/base_01/entrada/**/*.docx" in gitignore
    assert "tests/documentos_referencia/base_01/relatorios_avaliacao/**" in gitignore
    assert "!tests/documentos_referencia/base_01/checklist_humano/MODELO_CHECKLIST_REVISAO.csv" in gitignore


def test_legacy_base_collection_uses_old_input_dir(tmp_path, monkeypatch):
    pdf = tmp_path / "entrada" / "teste.pdf"
    pdf.parent.mkdir()
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(avaliar, "INPUT_DIR", pdf.parent)
    monkeypatch.setattr(avaliar, "CURRENT_BASE", None)
    assert avaliar.collect_documents() == [pdf]
