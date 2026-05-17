import argparse
import csv
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
DEFAULT_INPUT_DIR = REFERENCE_ROOT / "entrada"
DEFAULT_OUTPUT_DIR = REFERENCE_ROOT / "saida"
DEFAULT_REPORT_DIR = REFERENCE_ROOT / "relatorios_avaliacao"
DEFAULT_CHECKLIST_DIR = REFERENCE_ROOT / "checklist_humano"
INPUT_DIR = DEFAULT_INPUT_DIR
OUTPUT_DIR = DEFAULT_OUTPUT_DIR
REPORT_DIR = DEFAULT_REPORT_DIR
CHECKLIST_DIR = DEFAULT_CHECKLIST_DIR
CURRENT_BASE: str | None = None
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
CHECKLIST_COLUMNS = [
    "documento",
    "categoria",
    "codigo_apontamento",
    "trecho_original",
    "tipo",
    "gravidade",
    "origem",
    "status_humano",
    "comentario_humano",
]


def main() -> int:
    args = parse_args()
    configure_base(args.base)
    if args.api_summary:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = write_api_summary()
        print(f"Resumo API gerado em {path}")
        return 0
    if args.mode:
        os.environ["AI_MODE"] = args.mode
    app = create_app()
    ensure_directories()

    documents = collect_documents()
    if not documents:
        print(f"Nenhum PDF/DOCX encontrado em {INPUT_DIR}")
        if args.compare:
            path = write_compare_report([], [])
            print(f"Comparativo vazio gerado em {path}")
        return 0

    with app.app_context():
        if args.compare:
            mock_results = run_batch(documents, "mock")
            api_results = run_batch(documents, "api")
            path = write_compare_report(mock_results, api_results)
            print(f"Comparativo gerado em {path}")
            return 0

        mode = args.mode or app.config["AI_MODE"]
        for document in documents:
            result = evaluate_pdf(document, mode)
            report_path = REPORT_DIR / f"{report_stem(document)}_avaliacao_{mode}.json"
            report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{document.name}: {result['total_apontamentos']} apontamentos | relatório {report_path}")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Avalia a revisão de PDFs de referência.")
    parser.add_argument("--mode", choices=["mock", "api"], help="Modo de IA a usar nesta execução.")
    parser.add_argument("--compare", action="store_true", help="Roda mock e api e gera relatório comparativo.")
    parser.add_argument("--api-summary", action="store_true", help="Gera resumo consolidado a partir dos JSONs API existentes.")
    parser.add_argument("--base", help="Base de referência opcional, como base_01.")
    return parser.parse_args()


def configure_base(base_name: str | None) -> None:
    global INPUT_DIR, OUTPUT_DIR, REPORT_DIR, CHECKLIST_DIR, CURRENT_BASE
    if not base_name and CURRENT_BASE:
        INPUT_DIR = DEFAULT_INPUT_DIR
        OUTPUT_DIR = DEFAULT_OUTPUT_DIR
        REPORT_DIR = DEFAULT_REPORT_DIR
        CHECKLIST_DIR = DEFAULT_CHECKLIST_DIR
    CURRENT_BASE = base_name
    if not base_name:
        return
    base_root = REFERENCE_ROOT / base_name
    INPUT_DIR = base_root / "entrada"
    OUTPUT_DIR = base_root / "saida"
    REPORT_DIR = base_root / "relatorios_avaliacao"
    CHECKLIST_DIR = base_root / "checklist_humano"


def ensure_directories() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if CURRENT_BASE:
        CHECKLIST_DIR.mkdir(parents=True, exist_ok=True)


def collect_documents() -> list[Path]:
    if CURRENT_BASE:
        return sorted(
            path
            for path in INPUT_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    return sorted(path for path in INPUT_DIR.glob("*.pdf") if path.is_file())


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
        target_dir = output_dir_for(pdf_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        for file_row in generated:
            source = Path(file_row["path"])
            if source.exists():
                target = target_dir / source.name
                shutil.copy2(source, target)
                copied_files.append(str(target.relative_to(ROOT)))
        if CURRENT_BASE:
            write_document_checklist(pdf_path, document_id, issues)
    except Exception as exc:
        errors.append(str(exc))

    elapsed = round(time.perf_counter() - start, 2)
    by_type = Counter(issue.get("issue_type") for issue in issues)
    by_severity = Counter(issue.get("severity") for issue in issues)
    by_source = Counter(issue.get("source") for issue in issues)
    located = sum(1 for issue in issues if issue.get("located_in_pdf"))
    not_located = len(issues) - located
    risk = calculate_risk(by_severity, len(issues))
    categoria = category_for(pdf_path)

    return {
        "arquivo": pdf_path.name,
        "categoria": categoria,
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
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "possivel_excesso_falso_positivo": possible_false_positive_excess(categoria, by_severity, len(issues)),
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
                "estrategia_localizacao": issue.get("location_strategy"),
                "repeated_group_id": issue.get("repeated_group_id"),
                "repeated_count": issue.get("repeated_count"),
                "trecho": issue.get("original_text"),
                "sugestao": issue.get("suggestion"),
            }
            for issue in issues
        ],
    }


def category_for(path: Path) -> str:
    if not CURRENT_BASE:
        return "entrada"
    try:
        relative = path.relative_to(INPUT_DIR)
    except ValueError:
        return path.parent.name
    return relative.parts[0] if len(relative.parts) > 1 else "sem_categoria"


def report_stem(path: Path) -> str:
    category = category_for(path)
    return f"{category}__{path.stem}" if CURRENT_BASE else path.stem


def output_dir_for(path: Path) -> Path:
    if CURRENT_BASE:
        return OUTPUT_DIR / category_for(path) / path.stem
    return OUTPUT_DIR / path.stem


def calculate_risk(by_severity: Counter, total: int) -> dict:
    alta = by_severity.get("ALTA", 0)
    media = by_severity.get("MEDIA", 0)
    critica = by_severity.get("CRITICA", 0)
    conferir = by_severity.get("CONFERIR", 0)
    baixa = by_severity.get("BAIXA", 0)
    score = critica * 100 + alta * 20 + media * 8 + conferir * 5 + baixa * 2
    if total == 0:
        level = "SEM_APONTAMENTOS"
    elif critica or alta > 5:
        level = "CRITICO"
    elif 1 <= alta <= 5 or media >= 8:
        level = "ALTO"
    elif media or conferir:
        level = "MEDIO"
    else:
        level = "BAIXO"
    return {"risk_score": score, "risk_level": level}


def possible_false_positive_excess(category: str, by_severity: Counter, total: int) -> bool:
    if category != "documentos_bons":
        return False
    return bool(by_severity.get("ALTA", 0) or by_severity.get("CRITICA", 0) or total >= 5)


def write_document_checklist(pdf_path: Path, document_id: int | None, issues: list[dict]) -> None:
    CHECKLIST_DIR.mkdir(parents=True, exist_ok=True)
    target = CHECKLIST_DIR / f"checklist_{document_id or pdf_path.stem}.csv"
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHECKLIST_COLUMNS)
        writer.writeheader()
        for issue in issues:
            writer.writerow(
                {
                    "documento": pdf_path.name,
                    "categoria": category_for(pdf_path),
                    "codigo_apontamento": issue.get("code"),
                    "trecho_original": issue.get("original_text", ""),
                    "tipo": issue.get("issue_type"),
                    "gravidade": issue.get("severity"),
                    "origem": issue.get("source"),
                    "status_humano": "",
                    "comentario_humano": "",
                }
            )


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


def write_api_summary() -> Path:
    reports = sorted(REPORT_DIR.glob("*_avaliacao_api.json"))
    documents = []
    for report in reports:
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        documents.append(summary_document(data))
    summary = build_summary(documents)
    filename = (
        f"resumo_{CURRENT_BASE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if CURRENT_BASE
        else f"resumo_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    target = REPORT_DIR / filename
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def summary_document(data: dict) -> dict:
    return {
        "documento": data.get("arquivo"),
        "categoria": data.get("categoria", "entrada"),
        "total_apontamentos": data.get("total_apontamentos", 0),
        "origem": data.get("apontamentos_por_origem", {}),
        "gravidades": data.get("apontamentos_por_gravidade", {}),
        "tipos": data.get("apontamentos_por_tipo", {}),
        "localizados": data.get("trechos_localizados_pdf", 0),
        "nao_localizados": data.get("trechos_nao_localizados_pdf", 0),
        "risk_score": data.get("risk_score", 0),
        "risk_level": data.get("risk_level", "SEM_APONTAMENTOS"),
        "possivel_excesso_falso_positivo": data.get("possivel_excesso_falso_positivo", False),
        "erros_processamento": data.get("erros_processamento", []),
        "apontamentos": data.get("apontamentos", []),
        "principais_tipos": _top_items(data.get("apontamentos_por_tipo", {})),
        "principais_gravidades": _top_items(data.get("apontamentos_por_gravidade", {})),
    }


def build_summary(documents: list[dict]) -> dict:
    total_issues = sum(doc.get("total_apontamentos", 0) for doc in documents)
    by_category = Counter(doc.get("categoria", "entrada") for doc in documents)
    by_source = Counter()
    by_severity = Counter()
    by_type = Counter()
    recurring_texts = Counter()
    for doc in documents:
        by_source.update(doc.get("origem", {}))
        by_severity.update(doc.get("gravidades", {}))
        by_type.update(doc.get("tipos", {}))
        recurring_texts.update(
            " ".join(str(issue.get("trecho") or "").split())
            for issue in doc.get("apontamentos", [])
            if issue.get("trecho")
        )
    documentos_bons = [doc for doc in documents if doc.get("categoria") == "documentos_bons"]
    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "total_documentos": len(documents),
        "documentos_por_categoria": dict(sorted(by_category.items())),
        "total_apontamentos": total_issues,
        "media_apontamentos_por_documento": round(total_issues / len(documents), 2) if documents else 0,
        "total_por_origem": dict(sorted(by_source.items())),
        "total_por_gravidade": dict(sorted(by_severity.items())),
        "total_por_tipo": dict(sorted(by_type.items())),
        "total_localizados": sum(doc.get("localizados", 0) for doc in documents),
        "total_nao_localizados": sum(doc.get("nao_localizados", 0) for doc in documents),
        "documentos_com_erro_processamento": [doc["documento"] for doc in documents if doc.get("erros_processamento")],
        "documentos_com_muitos_apontamentos": [doc["documento"] for doc in documents if doc.get("total_apontamentos", 0) >= 20],
        "documentos_com_zero_apontamentos": [doc["documento"] for doc in documents if doc.get("total_apontamentos", 0) == 0],
        "documentos_com_possivel_excesso_falso_positivo": [
            doc["documento"] for doc in documents if doc.get("possivel_excesso_falso_positivo")
        ],
        "documentos_bons_com_0_apontamentos": [doc["documento"] for doc in documentos_bons if doc.get("total_apontamentos", 0) == 0],
        "documentos_bons_com_apontamentos_baixos": [
            doc["documento"]
            for doc in documentos_bons
            if 0 < doc.get("total_apontamentos", 0) < 5 and not doc.get("possivel_excesso_falso_positivo")
        ],
        "documentos_bons_com_apontamentos_altos_criticos": [
            doc["documento"]
            for doc in documentos_bons
            if doc.get("gravidades", {}).get("ALTA", 0) or doc.get("gravidades", {}).get("CRITICA", 0)
        ],
        "ranking_tipos_erro": dict(by_type.most_common(10)),
        "ranking_trechos_recorrentes": dict(recurring_texts.most_common(20)),
        "documentos": documents,
    }


def _top_items(counter: dict) -> dict:
    return dict(sorted((counter or {}).items(), key=lambda item: item[1], reverse=True)[:5])


if __name__ == "__main__":
    raise SystemExit(main())
