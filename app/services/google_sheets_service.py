import json
import re
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.hotel_repository import HotelRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.google_sheets import (
    GoogleSheetsExportHotelResult,
    GoogleSheetsExportRequest,
    GoogleSheetsExportResponse,
)
from app.services.translation_service import TranslationService


class GoogleSheetsService:
    default_sheet_title_map = {
        "ania_airport_residences_next_to_holiday_inn": "Ania Airport Residences",
        "luxury_private_pool_villas_village_danang_resort": "Luxury Pool Villas Danang",
        "republic_airport_residences": "Republic Airport Residences",
        "resort_pool_villa_beach_access_premier_village_dan": "Premier Village Beach Access",
        "resort_private_pool_villa_premier_village_danang": "Premier Village Private Pool",
        "the_grace_an_thuong_apartment": "The Grace An Thuong",
        "urbanr_danang_beach": "UrbanR Danang Beach",
    }
    header = [
        "hotel_name",
        "reviewed_at",
        "reviewer_name",
        "reviewer_country_code",
        "rating",
        "is_bad_review",
        "translated_title_vi",
        "translated_text_vi",
    ]
    sheets_api_base = "https://sheets.googleapis.com/v4/spreadsheets"
    token_url = "https://oauth2.googleapis.com/token"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.hotel_repository = HotelRepository(db)
        self.review_repository = ReviewRepository(db)
        self.translation_service = TranslationService()

    def export_reviews(self, payload: GoogleSheetsExportRequest) -> GoogleSheetsExportResponse:
        spreadsheet_id = payload.spreadsheet_id or settings.google_sheets_spreadsheet_id
        if not spreadsheet_id:
            raise ValueError("google spreadsheet id is required")

        if not settings.google_oauth_client_id:
            raise ValueError("google oauth client id is not configured")
        if not settings.google_oauth_client_secret:
            raise ValueError("google oauth client secret is not configured")
        if not settings.google_oauth_refresh_token:
            raise ValueError("google oauth refresh token is not configured")

        hotels = self.hotel_repository.list_export_hotels(
            hotel_ids=payload.hotel_ids or None,
            only_active_hotels=payload.only_active_hotels,
        )
        hotels = self._filter_enabled_hotels(
            hotels=hotels,
            only_enabled_hotels=payload.only_enabled_hotels,
        )

        access_token = self._refresh_access_token()
        existing_titles = self._get_sheet_titles(spreadsheet_id, access_token)

        exported_hotels: list[GoogleSheetsExportHotelResult] = []
        for hotel in hotels:
            sheet_title = self._resolve_sheet_title(hotel)
            if sheet_title not in existing_titles:
                self._create_sheet(spreadsheet_id, access_token, sheet_title)
                existing_titles.add(sheet_title)

            rows = self.review_repository.list_google_sheet_rows(hotel_id=hotel["id"])
            rows = self._hydrate_missing_translations(rows)
            values = [self.header] + [self._map_row(row) for row in rows]

            if payload.replace_sheet:
                self._clear_sheet(spreadsheet_id, access_token, sheet_title)
            self._update_sheet_values(spreadsheet_id, access_token, sheet_title, values)

            exported_hotels.append(
                GoogleSheetsExportHotelResult(
                    hotel_id=hotel["id"],
                    hotel_name=hotel["hotel_name"],
                    sheet_title=sheet_title,
                    exported_rows=len(rows),
                )
            )

        return GoogleSheetsExportResponse(
            spreadsheet_id=spreadsheet_id,
            exported_hotels=exported_hotels,
            total_hotels=len(exported_hotels),
        )

    def _filter_enabled_hotels(
        self,
        *,
        hotels: list[dict[str, Any]],
        only_enabled_hotels: bool,
    ) -> list[dict[str, Any]]:
        if not only_enabled_hotels:
            return hotels

        filtered: list[dict[str, Any]] = []
        for hotel in hotels:
            metadata = hotel.get("metadata") or {}
            if metadata.get("google_sheet_sync_enabled", True):
                filtered.append(hotel)
        return filtered

    def _refresh_access_token(self) -> str:
        payload = {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "refresh_token": settings.google_oauth_refresh_token,
            "grant_type": "refresh_token",
        }
        request = Request(
            url=self.token_url,
            data="&".join(f"{key}={quote(str(value))}" for key, value in payload.items()).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ValueError(f"failed to refresh google access token: {exc}") from exc

        access_token = body.get("access_token")
        if not access_token:
            raise ValueError("google token response did not include access_token")
        return access_token

    def _get_sheet_titles(self, spreadsheet_id: str, access_token: str) -> set[str]:
        response = self._request_json(
            method="GET",
            url=f"{self.sheets_api_base}/{spreadsheet_id}?fields=sheets.properties.title",
            access_token=access_token,
        )
        return {
            sheet.get("properties", {}).get("title")
            for sheet in response.get("sheets", [])
            if sheet.get("properties", {}).get("title")
        }

    def _create_sheet(self, spreadsheet_id: str, access_token: str, sheet_title: str) -> None:
        self._request_json(
            method="POST",
            url=f"{self.sheets_api_base}/{spreadsheet_id}:batchUpdate",
            access_token=access_token,
            body={
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": sheet_title,
                            }
                        }
                    }
                ]
            },
        )

    def _clear_sheet(self, spreadsheet_id: str, access_token: str, sheet_title: str) -> None:
        escaped = quote(f"{sheet_title}!A:Z", safe="!:'")
        self._request_json(
            method="POST",
            url=f"{self.sheets_api_base}/{spreadsheet_id}/values/{escaped}:clear",
            access_token=access_token,
            body={},
        )

    def _update_sheet_values(
        self,
        spreadsheet_id: str,
        access_token: str,
        sheet_title: str,
        values: list[list[Any]],
    ) -> None:
        escaped = quote(f"{sheet_title}!A1", safe="!:'")
        self._request_json(
            method="PUT",
            url=f"{self.sheets_api_base}/{spreadsheet_id}/values/{escaped}?valueInputOption=USER_ENTERED",
            access_token=access_token,
            body={
                "range": f"{sheet_title}!A1",
                "majorDimension": "ROWS",
                "values": values,
            },
        )

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        access_token: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            url=url,
            data=data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            method=method,
        )
        try:
            with urlopen(request, timeout=60) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"google sheets api error: {detail or exc.reason}") from exc
        except (URLError, TimeoutError) as exc:
            raise ValueError(f"google sheets request failed: {exc}") from exc

        if not response_body:
            return {}
        try:
            return json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ValueError("google sheets returned invalid json") from exc

    def _resolve_sheet_title(self, hotel: dict[str, Any]) -> str:
        metadata = hotel.get("metadata") or {}
        title = (
            metadata.get("sheet_tab_name")
            or metadata.get("google_sheet_tab_name")
            or self.default_sheet_title_map.get(hotel.get("hotel_code", ""))
            or hotel.get("hotel_name")
            or hotel.get("hotel_code")
            or hotel.get("id")
        )
        title = re.sub(r"[\[\]\*\?/\\:]", " ", str(title)).strip()
        title = re.sub(r"\s+", " ", title)
        return title[:100] or hotel["id"]

    def _hydrate_missing_translations(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        changed = False
        for row in rows:
            corrected_bad_flag = self._compute_bad_review(row)
            if row.get("is_bad_review") != corrected_bad_flag:
                row["is_bad_review"] = corrected_bad_flag
                self.review_repository.update_review_bad_flag(
                    review_id=row["review_id"],
                    is_bad_review=corrected_bad_flag,
                )
                changed = True

            if self._has_translation(row):
                continue
            review_title = row.get("review_title")
            review_text = row.get("review_text")
            if not review_title and not review_text:
                continue
            try:
                enriched = self.translation_service.enrich_review_translation(
                    {
                        "review_title": review_title,
                        "review_text": review_text,
                        "review_language": row.get("review_language"),
                        "normalized_payload": {},
                    }
                )
                normalized_payload = enriched.get("normalized_payload") or {}
                row["translated_title_vi"] = normalized_payload.get("translated_title_vi")
                row["translated_text_vi"] = normalized_payload.get("translated_text_vi")
                if not row.get("translated_title_vi") and self._should_fallback_to_original(row, review_title):
                    row["translated_title_vi"] = review_title
                if not row.get("translated_text_vi") and self._should_fallback_to_original(row, review_text):
                    row["translated_text_vi"] = review_text
                if row.get("translated_title_vi") or row.get("translated_text_vi"):
                    self.review_repository.update_review_translations(
                        review_id=row["review_id"],
                        translated_title_vi=row.get("translated_title_vi"),
                        translated_text_vi=row.get("translated_text_vi"),
                        translation_provider=normalized_payload.get("translation_provider"),
                        translation_target_language=normalized_payload.get("translation_target_language"),
                        translation_detected_source_language=normalized_payload.get(
                            "translation_detected_source_language"
                        ),
                    )
                    changed = True
            except Exception:
                self.db.rollback()
                continue
        if changed:
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
        return rows

    @staticmethod
    def _compute_bad_review(row: dict[str, Any]) -> bool:
        rating = row.get("rating")
        if rating is None:
            return bool(row.get("is_bad_review"))
        return float(rating) < settings.bad_review_rating_threshold

    @staticmethod
    def _has_translation(row: dict[str, Any]) -> bool:
        review_language = (row.get("review_language") or "").strip().lower()
        title = (row.get("review_title") or "").strip()
        text = (row.get("review_text") or "").strip()
        translated_title = (row.get("translated_title_vi") or "").strip()
        translated_text = (row.get("translated_text_vi") or "").strip()

        title_ok = not title or (
            translated_title
            and (review_language == "vi" or translated_title != title)
        )
        text_ok = not text or (
            translated_text
            and (review_language == "vi" or translated_text != text)
        )
        return title_ok and text_ok

    @staticmethod
    def _should_fallback_to_original(row: dict[str, Any], value: str | None) -> bool:
        if not value:
            return False
        review_language = (row.get("review_language") or "").strip().lower()
        return review_language in {"", "vi", "vi-vn"}

    def _map_row(self, row: dict[str, Any]) -> list[Any]:
        reviewed_at = row.get("reviewed_at")
        if isinstance(reviewed_at, datetime):
            reviewed_at_value = reviewed_at.isoformat()
        else:
            reviewed_at_value = reviewed_at
        return [
            row.get("hotel_name"),
            reviewed_at_value,
            row.get("reviewer_name"),
            row.get("reviewer_country_code"),
            row.get("rating"),
            row.get("is_bad_review"),
            row.get("translated_title_vi"),
            row.get("translated_text_vi"),
        ]
