from __future__ import annotations

import argparse
from pathlib import Path

from api_doc_support import load_fastapi_endpoints, project_root, render_endpoint_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate API endpoint docs from FastAPI routes.")
    parser.add_argument(
        "--output",
        default=str(project_root() / "docs" / "API_ENDPOINTS.md"),
        help="Path to the generated markdown file.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_endpoint_markdown(load_fastapi_endpoints()), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
