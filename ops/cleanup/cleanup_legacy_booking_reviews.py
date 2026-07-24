from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text

from app.db.session import SessionLocal


MATCH_SQL = """
WITH candidate_pairs AS (
    SELECT
        legacy.id::text AS legacy_review_id,
        real.id::text AS real_review_id,
        legacy.hotel_id::text AS hotel_id,
        legacy.external_review_id AS legacy_external_review_id,
        real.external_review_id AS real_external_review_id,
        legacy.reviewer_name,
        legacy.review_title,
        legacy.review_text,
        legacy.rating,
        legacy.reviewed_at,
        ROW_NUMBER() OVER (
            PARTITION BY legacy.id
            ORDER BY real.reviewed_at DESC, real.created_at DESC
        ) AS canonical_rank,
        COUNT(*) OVER (PARTITION BY legacy.id) AS canonical_count
    FROM reviews legacy
    JOIN platforms p
      ON p.id = legacy.platform_id
    JOIN reviews real
      ON real.hotel_id = legacy.hotel_id
     AND real.platform_id = legacy.platform_id
     AND real.id <> legacy.id
     AND real.external_review_id NOT LIKE 'booking-visible-%'
     AND lower(trim(coalesce(real.reviewer_name, ''))) = lower(trim(coalesce(legacy.reviewer_name, '')))
     AND lower(trim(coalesce(real.review_title, ''))) = lower(trim(coalesce(legacy.review_title, '')))
     AND lower(trim(coalesce(real.review_text, ''))) = lower(trim(coalesce(legacy.review_text, '')))
     AND coalesce(real.rating, -1) = coalesce(legacy.rating, -1)
     AND coalesce(real.rating_scale, -1) = coalesce(legacy.rating_scale, -1)
     AND real.reviewed_at::date = legacy.reviewed_at::date
    WHERE p.platform_code = :platform_code
      AND legacy.external_review_id LIKE 'booking-visible-%'
      AND (:hotel_id IS NULL OR legacy.hotel_id = CAST(:hotel_id AS uuid))
),
safe_matches AS (
    SELECT
        legacy_review_id,
        real_review_id,
        hotel_id,
        legacy_external_review_id,
        real_external_review_id,
        reviewer_name,
        review_title,
        review_text,
        rating,
        reviewed_at,
        canonical_count
    FROM candidate_pairs
    WHERE canonical_rank = 1
      AND canonical_count = 1
)
SELECT *
FROM safe_matches
ORDER BY hotel_id, reviewed_at, legacy_review_id
"""


DELETE_SQL = """
DELETE FROM reviews
WHERE id = CAST(:legacy_review_id AS uuid)
RETURNING
    id::text AS deleted_review_id,
    external_review_id,
    hotel_id::text AS hotel_id
"""


@dataclass
class CleanupResult:
    matches: list[dict[str, Any]]
    deleted: list[dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect and optionally delete legacy booking-visible duplicate reviews."
    )
    parser.add_argument("--hotel-id", help="Only process one hotel_id", default=None)
    parser.add_argument("--platform-code", default="booking")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete matched legacy reviews. Default is dry-run.",
    )
    parser.add_argument(
        "--report-json",
        default=None,
        help="Optional path to write the detection report as JSON.",
    )
    parser.add_argument(
        "--report-csv",
        default=None,
        help="Optional path to write the detection report as CSV.",
    )
    return parser.parse_args()


def detect_matches(hotel_id: str | None, platform_code: str) -> list[dict[str, Any]]:
    with SessionLocal() as db:
        rows = db.execute(
            text(MATCH_SQL),
            {
                "hotel_id": hotel_id,
                "platform_code": platform_code,
            },
        ).mappings().all()
        return [dict(row) for row in rows]


def delete_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deleted: list[dict[str, Any]] = []
    with SessionLocal() as db:
        for match in matches:
            row = db.execute(
                text(DELETE_SQL),
                {"legacy_review_id": match["legacy_review_id"]},
            ).mappings().first()
            if row:
                deleted.append(dict(row))
        db.commit()
    return deleted


def write_json_report(path: str, payload: dict[str, Any]) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_report(path: str, rows: list[dict[str, Any]]) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        report_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with report_path.open("w", newline="", encoding="utf-8-sig") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(result: CleanupResult, execute: bool) -> None:
    print("=== Legacy Booking Cleanup ===")
    print(f"safe_matches: {len(result.matches)}")
    print(f"mode: {'execute-delete' if execute else 'dry-run'}")
    if result.matches:
        print("")
        print("Sample matches:")
        for item in result.matches[:10]:
            print(
                json.dumps(
                    {
                        "hotel_id": item["hotel_id"],
                        "legacy_review_id": item["legacy_review_id"],
                        "legacy_external_review_id": item["legacy_external_review_id"],
                        "real_review_id": item["real_review_id"],
                        "real_external_review_id": item["real_external_review_id"],
                        "reviewer_name": item["reviewer_name"],
                        "rating": item["rating"],
                        "reviewed_at": str(item["reviewed_at"]),
                    },
                    ensure_ascii=False,
                )
            )
    if execute:
        print("")
        print(f"deleted_rows: {len(result.deleted)}")


def main() -> None:
    args = parse_args()
    matches = detect_matches(
        hotel_id=args.hotel_id,
        platform_code=args.platform_code,
    )
    deleted: list[dict[str, Any]] = []

    if args.execute and matches:
        deleted = delete_matches(matches)

    result = CleanupResult(matches=matches, deleted=deleted)
    print_summary(result, args.execute)

    report_payload = {
        "platform_code": args.platform_code,
        "hotel_id": args.hotel_id,
        "mode": "execute-delete" if args.execute else "dry-run",
        "safe_match_count": len(matches),
        "deleted_count": len(deleted),
        "matches": matches,
        "deleted": deleted,
    }

    if args.report_json:
        write_json_report(args.report_json, report_payload)

    if args.report_csv:
        write_csv_report(args.report_csv, matches)


if __name__ == "__main__":
    main()
