import html
import asyncio
import importlib
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class TranslationService:
    translate_url = "https://translation.googleapis.com/language/translate/v2"
    valid_language_pattern = re.compile(r"^[a-z]{2,3}(-[a-z]{2,4})?$")

    def __init__(self) -> None:
        self.provider = settings.translation_provider.lower().strip()
        self.google_api_enabled = settings.google_translate_enabled and bool(settings.google_translate_api_key)
        self.googletrans_translator_cls = None
        self.googletrans_available = self._load_googletrans()
        self.enabled = self.provider in {"google_api", "googletrans"} or self.google_api_enabled
        self.api_key = settings.google_translate_api_key
        self.target_language = settings.google_translate_target_language
        self.timeout_seconds = settings.google_translate_timeout_seconds

    def _load_googletrans(self) -> bool:
        try:
            module = importlib.import_module("googletrans")
            self.googletrans_translator_cls = getattr(module, "Translator", None)
            return self.googletrans_translator_cls is not None
        except Exception:
            self.googletrans_translator_cls = None
            return False

    def enrich_review_translation(self, review: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return review

        normalized_payload = dict(review.get("normalized_payload") or {})
        review_language = review.get("review_language")

        title = review.get("review_title")
        text = review.get("review_text")

        translations: dict[str, str] = {}
        translated_source_language: str | None = None

        if title:
            translated_title, detected = self._translate_text(title, review_language)
            translations["translated_title_vi"] = translated_title
            translated_source_language = translated_source_language or detected

        if text:
            translated_text, detected = self._translate_text(text, review_language)
            translations["translated_text_vi"] = translated_text
            translated_source_language = translated_source_language or detected

        if translations:
            normalized_payload.update(translations)
            normalized_payload["translation_provider"] = self._resolved_provider_name()
            normalized_payload["translation_target_language"] = self.target_language
            if translated_source_language:
                normalized_payload["translation_detected_source_language"] = translated_source_language
            review["normalized_payload"] = normalized_payload

        return review

    def _translate_text(self, text: str, source_language: str | None) -> tuple[str, str | None]:
        cleaned_text = text.strip()
        if not cleaned_text:
            return text, source_language

        source_language = self._normalize_source_language(source_language)

        if source_language and source_language.lower() == self.target_language.lower():
            return cleaned_text, source_language

        if self._use_googletrans():
            translated_text, detected_language = self._translate_with_googletrans(cleaned_text, source_language)
            return translated_text, detected_language

        if not self.google_api_enabled:
            return cleaned_text, source_language

        payload: dict[str, Any] = {
            "q": cleaned_text,
            "target": self.target_language,
            "format": "text",
        }
        if source_language:
            payload["source"] = source_language

        request = Request(
            url=f"{self.translate_url}?key={self.api_key}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return cleaned_text, source_language

        translations = body.get("data", {}).get("translations", [])
        if not translations:
            return cleaned_text, source_language

        first = translations[0]
        translated_text = html.unescape(first.get("translatedText") or cleaned_text)
        detected_source_language = first.get("detectedSourceLanguage") or source_language
        return translated_text, detected_source_language

    def _use_googletrans(self) -> bool:
        return self.provider == "googletrans" and self.googletrans_available

    def _resolved_provider_name(self) -> str:
        if self._use_googletrans():
            return "googletrans"
        if self.google_api_enabled:
            return "google_cloud_translation"
        return "disabled"

    def _translate_with_googletrans(self, text: str, source_language: str | None) -> tuple[str, str | None]:
        if self.googletrans_translator_cls is None:
            return text, source_language

        try:
            result = asyncio.run(self._translate_with_googletrans_async(text, source_language))
            translated_text = getattr(result, "text", None) or text
            detected_source_language = getattr(result, "src", None) or source_language
            return translated_text, detected_source_language
        except Exception:
            return text, source_language

    async def _translate_with_googletrans_async(self, text: str, source_language: str | None) -> Any:
        translator = self.googletrans_translator_cls(service_urls=["translate.googleapis.com"])
        src = source_language if source_language else "auto"
        return await translator.translate(text, src=src, dest=self.target_language)

    def _normalize_source_language(self, source_language: str | None) -> str | None:
        if not source_language:
            return None

        normalized = source_language.strip().lower()
        if normalized in {"auto", "und", "unknown", "xt", "xu", "xx", "mul", "other"}:
            return None

        if not self.valid_language_pattern.match(normalized):
            return None

        return normalized
