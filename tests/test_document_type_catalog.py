from pathlib import Path

from app import create_app
from app.document_types.catalog import (
    get_all_document_types,
    get_document_type,
    get_document_types_by_group,
    get_document_types_by_user_group,
    get_generation_ready_types,
    get_review_ready_types,
    get_types_for_creation_menu,
    get_user_groups,
    search_document_types,
    validate_catalog_shape,
)


def test_catalog_loads_and_codes_are_unique():
    items = get_all_document_types()
    codes = [item["code"] for item in items]
    assert len(items) >= 30
    assert len(codes) == len(set(codes))
    assert validate_catalog_shape() == []


def test_catalog_required_public_fields_are_present():
    for item in get_all_document_types():
        assert item["code"]
        assert item["user_label"]
        assert item["user_group"]
        assert item["required_fields"]
        assert item["output_documents"]
        assert item["risk_points"]


def test_required_initial_document_types_exist():
    constituicao = get_document_type("CONSTITUICAO_LTDA")
    ata = get_document_type("ATA_AGE")
    assert constituicao is not None
    assert constituicao["user_label"] == "Constituição de LTDA"
    assert constituicao["form_blocks"]
    assert ata is not None
    assert ata["user_group"] == "Ata / Assembleia"


def test_catalog_group_filters_and_ready_flags():
    assert get_document_types_by_group("LTDA")
    assert get_document_types_by_user_group("Contrato Social / LTDA")
    assert get_review_ready_types()
    assert get_generation_ready_types() == []


def test_catalog_search_and_creation_menu():
    results = search_document_types("constituição")
    assert any(item["code"] == "CONSTITUICAO_LTDA" for item in results)
    groups = get_user_groups()
    menu = get_types_for_creation_menu()
    assert "Contrato Social / LTDA" in groups
    assert all(group["user_group"] and group["types"] for group in menu)


def _test_app(tmp_path, monkeypatch):
    db_path = tmp_path / "test_catalog_routes.db"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(db_path).replace("\\", "/"))
    monkeypatch.setenv("AI_MODE", "mock")
    return create_app()


def test_generation_menu_route_loads(tmp_path, monkeypatch):
    app = _test_app(tmp_path, monkeypatch)
    client = app.test_client()
    response = client.get("/generation/")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Criar nova minuta ou ata" in text
    assert "Constituição de LTDA" in text


def test_generation_type_detail_route_loads(tmp_path, monkeypatch):
    app = _test_app(tmp_path, monkeypatch)
    client = app.test_client()
    response = client.get("/generation/type/CONSTITUICAO_LTDA")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Constituição de LTDA" in text
    assert "Formulário preparatório" in text
    assert "Razão social" in text
    assert "Geração real prevista para V5.1" in text


def test_generation_type_not_found_is_friendly(tmp_path, monkeypatch):
    app = _test_app(tmp_path, monkeypatch)
    client = app.test_client()
    response = client.get("/generation/type/NAO_EXISTE")
    assert response.status_code == 404
    text = response.get_data(as_text=True)
    assert "Tipo documental não encontrado" in text
    assert "Voltar ao catálogo" in text


def test_existing_review_upload_route_still_loads(tmp_path, monkeypatch):
    app = _test_app(tmp_path, monkeypatch)
    client = app.test_client()
    response = client.get("/documents/upload")
    assert response.status_code == 200


def test_project_docs_mention_ocr_decision():
    text = Path("docs/DOCUMENT_TYPE_CATALOG.md").read_text(encoding="utf-8")
    assert "OCR nunca será fonte automática definitiva" in text
    assert "CONSTITUICAO_LTDA" in text
