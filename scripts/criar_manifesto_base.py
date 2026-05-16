import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = ROOT / "tests" / "documentos_referencia"
DEFAULT_BASE = "base_01"
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def main() -> int:
    args = parse_args()
    base_dir = REFERENCE_ROOT / args.base
    input_dir = base_dir / "entrada"
    report_dir = base_dir / "relatorios_avaliacao"
    input_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(input_dir)
    target = report_dir / f"manifesto_{args.base}.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifesto gerado em {target}")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Cria manifesto local da base de referência.")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Nome da base em tests/documentos_referencia.")
    return parser.parse_args()


def build_manifest(input_dir: Path) -> dict:
    now = datetime.now().isoformat(timespec="seconds")
    files = []
    for index, path in enumerate(iter_reference_documents(input_dir), start=1):
        files.append(
            {
                "id_local": f"DOC{index:04d}",
                "nome_arquivo": path.name,
                "categoria": path.parent.name,
                "extensao": path.suffix.lower(),
                "tamanho_aproximado_bytes": path.stat().st_size,
                "data_processamento": now,
                "hash_local": file_hash(path),
                "status_inicial": "PENDENTE",
                "observacoes": "",
            }
        )
    return {
        "base": input_dir.parent.name,
        "gerado_em": now,
        "total_arquivos": len(files),
        "arquivos": files,
    }


def iter_reference_documents(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
