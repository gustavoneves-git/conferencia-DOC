import argparse
import json
import os
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from flask import current_app

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.repositories.document_repository import DocumentRepository
from app.repositories.generated_file_repository import GeneratedFileRepository
from app.repositories.review_repository import ReviewRepository
from app.services.review_orchestrator_service import ReviewOrchestratorService


REFERENCE_ROOT = ROOT / "tests" / "documentos_referencia"
INPUT_DIR = REFERENCE_ROOT / "entrada"
OUTPUT_DIR = REFERENCE_ROOT / "saida"
REPORT_DIR = REFERENCE_ROOT / "relatorios_avaliacao"


def main() -> int:
    args = parse_args()
    if args.mode:
        os.environ["AI_MODE"] = args.mode
    app = create_app()
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF encontrado em {INPUT_DIR}")
        if args.compare:
            path = write_compare_report([], [])
            print(f"Comparativo vazio gerado em {path}")
        return 0

    with app.app_context():
        if args.compare:
            mock_results = run_batch(pdfs, "mock")
            api_results = run_batch(pdfs, "api")
            path = write_compare_report(mock_results, api_results)
            print(f"Comparativo gerado em {path}")
            return 0

        mode = args.mode or app.config["AI_MODE"]
        for pdf in pdfs:
            result = evaluate_pdf(pdf, mode)
            report_path = REPORT_DIR / f"{pdf.stem}_avaliacao_{mode}.json"
            report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{pdf.name}: {result['total_apontamentos']} apontamentos | relatório {report_path}")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Avalia a revisão de PDFs de referência.")
    parser.add_argument("--mode", choices=["mock", "api"], help="Modo de IA a usar nesta execução.")
    parser.add_argument("--compare", action="store_true", help="Roda mock e api e gera relatório comparativo.")
    return parser.parse_args()


def run_batch(pdfs: list[Path], mode: str) -> list[dict]:
    previous = os.environ.get("AI_MODE")
    previous_config = current_app.config.get("AI_MODE")
    os.environ["AI_MODE"] = mode
    current_app.config["AI_MODE"] = mode
    results = [evaluate_pdf(pdf, mode) for pdf in pdfs]
    current_app.config["AI_MODE"] = previous_config
    if previous is None:
        os.environ.pop("AI_MODE", None)
    else:
        os.environ["AI_MODE"] = previous
    return results


def evaluate_pdf(pdf_path: Path, mode: str | None = None) -> dict:
    start = time.perf_counter()
    errors = []
    copied_files = []
    document_id = None
    session_id = None
    issues = []
    document_row = None

    try:
        docs = DocumentRepository()
        document_id = docs.create(pdf_path.name, pdf_path.name, str(pdf_path), None)
        session_id = ReviewOrchestratorService().run(document_id)
        document_row = docs.get(document_id)
        issues = [dict(row) for row in ReviewRepository().issues(session_id)]
        generated = GeneratedFileRepository().list_for_document(document_id)
        target_dir = OUTPUT_DIR / pdf_path.stem
        target_dir.mkdir(parents=True, exist_ok=True)
        for file_row in generated:
            source = Path(file_row["path"])
            if source.exists():
                target = target_dir / f"{file_row['file_type'].lower()}_{source.name}"
                shutil.copy2(source, target)
                copied_files.append(str(target.relative_to(ROOT)))
    except Exception as exc:
        errors.append(str(exc))

    elapsed = round(time.perf_counter() - start, 2)
    by_type = Counter(issue.get("issue_type") for issue in issues)
    by_severity = Counter(issue.get("severity") for issue in issues)
    by_source = Counter(issue.get("source") for issue in issues)
    located = sum(1 for issue in issues if issue.get("located_in_pdf"))
    not_located = len(issues) - located

    return {
        "arquivo": pdf_path.name,
        "modo": mode,
        "document_id": document_id,
        "review_session_id": session_id,
        "tipo_documental_estimado": document_row["document_type"] if document_row else None,
        "empresa_identificada": document_row["company_name"] if document_row else None,
        "total_apontamentos": len(issues),
        "apontamentos_por_tipo": dict(sorted(by_type.items())),
        "apontamentos_por_gravidade": dict(sorted(by_severity.items())),
        "apontamentos_por_origem": dict(sorted(by_source.items())),
        "trechos_localizados_pdf": located,
        "trechos_nao_localizados_pdf": not_located,
        "arquivos_gerados": copied_files,
        "erros_processamento": errors,
        "tempo_execucao_segundos": elapsed,
        "apontamentos": [
            {
                "codigo": issue.get("code"),
                "pagina": issue.get("page_number"),
                "tipo": issue.get("issue_type"),
                "gravidade": issue.get("severity"),
                "fonte": issue.get("source"),
                "localizado_pdf": bool(issue.get("located_in_pdf")),
                "trecho": issue.get("original_text"),
                "sugestao": issue.get("suggestion"),
            }
            for issue in issues
        ],
    }


def write_compare_report(mock_results: list[dict], api_results: list[dict]) -> Path:
    by_api = {item["arquivo"]: item for item in api_results}
    documents = []
    for mock in mock_results:
        api = by_api.get(mock["arquivo"], empty_result(mock["arquivo"]))
        documents.append(compare_document(mock, api))
    for api in api_results:
        if api["arquivo"] not in {item["arquivo"] for item in mock_results}:
            documents.append(compare_document(empty_result(api["arquivo"]), api))

    report = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "total_documentos": len(documents),
        "documentos": documents,
    }
    target = REPORT_DIR / f"comparativo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def compare_document(mock: dict, api: dict) -> dict:
    mock_keys = {issue_key(item): item for item in mock.get("apontamentos", [])}
    api_keys = {issue_key(item): item for item in api.get("apontamentos", [])}
    only_rule = [mock_keys[key] for key in sorted(mock_keys.keys() - api_keys.keys())]
    only_api = [api_keys[key] for key in sorted(api_keys.keys() - mock_keys.keys())]
    both = [mock_keys[key] for key in sorted(mock_keys.keys() & api_keys.keys())]
    return {
        "arquivo": mock.get("arquivo") or api.get("arquivo"),
        "mock_total": mock.get("total_apontamentos", 0),
        "api_total": api.get("total_apontamentos", 0),
        "somente_rule": len(only_rule),
        "somente_api": len(only_api),
        "em_ambos": len(both),
        "duplicidades_removidas_estimadas": max(0, mock.get("total_apontamentos", 0) + api.get("total_apontamentos", 0) - len(set(mock_keys) | set(api_keys))),
        "mock_por_gravidade": mock.get("apontamentos_por_gravidade", {}),
        "api_por_gravidade": api.get("apontamentos_por_gravidade", {}),
        "mock_por_origem": mock.get("apontamentos_por_origem", {}),
        "api_por_origem": api.get("apontamentos_por_origem", {}),
        "mock_nao_localizados": mock.get("trechos_nao_localizados_pdf", 0),
        "api_nao_localizados": api.get("trechos_nao_localizados_pdf", 0),
        "erros_mock": mock.get("erros_processamento", []),
        "erros_api": api.get("erros_processamento", []),
        "amostras_somente_rule": only_rule[:20],
        "amostras_somente_api": only_api[:20],
    }


def issue_key(issue: dict) -> str:
    text = " ".join(str(issue.get("trecho") or "").lower().split())
    return f"{issue.get('pagina')}|{issue.get('tipo')}|{text[:120]}"


def empty_result(filename: str) -> dict:
    return {
        "arquivo": filename,
        "total_apontamentos": 0,
        "apontamentos": [],
        "apontamentos_por_gravidade": {},
        "apontamentos_por_origem": {},
        "trechos_nao_localizados_pdf": 0,
        "erros_processamento": [],
    }


if __name__ == "__main__":
    raise SystemExit(main())
