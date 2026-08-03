import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.schemas.review_insight import ReviewInsightRequest, ReviewInsightResponse
from app.services.admin_settings_service import AdminSettingsService


class ReviewInsightService:
    def __init__(self, db: Session) -> None:
        self.admin_settings_service = AdminSettingsService(db)

    def generate(self, payload: ReviewInsightRequest) -> ReviewInsightResponse:
        if not payload.reviews:
            return ReviewInsightResponse(
                content="Chua co review nao trong tap du lieu dang loc, nen AI chua the dua ra nhan dinh co y nghia."
            )

        config = self.admin_settings_service.get_review_ai_runtime_config()
        base_url = str(config["base_url"]).strip()
        api_key = str(config["api_key"]).strip()
        model = str(config["model"]).strip()
        timeout_ms = int(config["timeout_ms"])

        if not base_url or not api_key or not model:
            raise ValueError("Review AI is not configured in Admin > Settings.")

        request_payload = {
            "model": model,
            "temperature": 0.2,
            "max_tokens": 900,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Vietnamese review analyst. "
                        "Always answer in Vietnamese, practical, evidence-based, concise but useful."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_prompt(payload),
                },
            ],
        }

        body = json.dumps(request_payload).encode("utf-8")
        request = Request(
            url=f"{base_url.rstrip('/')}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "JoyON-Review-AI/1.0",
                "Origin": "https://data.datac.click",
                "Referer": "https://data.datac.click/",
            },
        )

        try:
            with urlopen(request, timeout=max(timeout_ms / 1000, 1)) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ValueError(f"Review AI request failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise ValueError(f"Review AI connection failed: {exc.reason}") from exc

        content = (
            response_payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        return ReviewInsightResponse(
            content=content or "AI da nhan request nhung chua tra ve noi dung phan tich co the hien thi."
        )

    def _build_prompt(self, payload: ReviewInsightRequest) -> str:
        return "\n".join(
            [
                "Ban la chuyen gia van hanh khach san va phan tich review.",
                "Hay phan tich dung tren du lieu da loc, viet bang tieng Viet, ro rang, thuc dung, khong viet chung chung.",
                "Chi duoc dua tren du lieu duoc cung cap. Neu du lieu it thi phai noi ro do la mau nho.",
                "",
                "Yeu cau dinh dang:",
                "1. Tong quan ngan",
                "2. Van de chinh can khac phuc",
                "3. Uu tien hanh dong ngay",
                "4. Tin hieu can theo doi them",
                "",
                "Quy tac:",
                "- Neu co category score thi chi ra category nao yeu nhat va category nao tot nhat.",
                "- Neu co bad review thi neu ro nhom van de lap lai.",
                "- Neu tap review hien tai chi la mau hien thi, phai noi ro do la mau dang xem tren man hinh.",
                "- Uu tien de xuat hanh dong cu the cho team van hanh, le tan, housekeeping, phong, wifi, vi tri, pricing neu co dau hieu.",
                "- Khong chen markdown phuc tap. Chi dung van ban thuong, xuong dong ro rang.",
                "",
                "Du lieu dau vao:",
                payload.model_dump_json(),
            ]
        )
