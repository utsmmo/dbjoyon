from __future__ import annotations

import argparse
import re
from pathlib import Path

from api_doc_support import load_fastapi_endpoints, project_root


ROW_PATTERN = re.compile(r"^\|\s*([A-Z]+)\s*\|\s*`([^`]+)`\s*\|", re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check drift between code routes and API endpoint docs.")
    parser.add_argument(
        "--doc",
        default=str(project_root() / "docs" / "API_ENDPOINTS.md"),
        help="Path to the generated markdown file.",
    )
    args = parser.parse_args()

    doc_path = Path(args.doc)
    if not doc_path.exists():
        print(f"Missing doc file: {doc_path}")
        return 1

    code_signatures = {endpoint.signature for endpoint in load_fastapi_endpoints()}
    doc_text = doc_path.read_text(encoding="utf-8")
    doc_signatures = {f"{method} {path}" for method, path in ROW_PATTERN.findall(doc_text)}

    missing_in_doc = sorted(code_signatures - doc_signatures)
    stale_in_doc = sorted(doc_signatures - code_signatures)

    if not missing_in_doc and not stale_in_doc:
        print("API_DOCS_OK")
        return 0

    if missing_in_doc:
        print("Missing in docs:")
        for item in missing_in_doc:
            print(f"- {item}")
    if stale_in_doc:
        print("Stale in docs:")
        for item in stale_in_doc:
            print(f"- {item}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
