from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib import request


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Purge all hotels and import a fresh hotel manifest into the API."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:13000",
        help="API base URL, for example http://localhost:13000 or https://data.datac.click",
    )
    parser.add_argument(
        "--manifest",
        default=str(Path(__file__).resolve().parent / "raon_hotel_import_manifest.json"),
        help="Path to the import manifest JSON file.",
    )
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    payload = {
        "confirm_purge": True,
        "hotels": manifest,
    }
    url = args.base_url.rstrip("/") + "/api/v1/system/hotels/reset-import"
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req) as response:
        print(response.read().decode("utf-8"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
