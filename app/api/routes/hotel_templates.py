from __future__ import annotations

import html
import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/hotel-templates", tags=["hotel-templates"])

DEFAULT_TEMPLATE = """Dear **(Guest Name),**

Thank you for choosing **(Property Name)** for your stay.

We are pleased to confirm your reservation with the following details:

• Booking Name: **(Guest Name)**
• Room/Villa Type: **(Room Type)**
• Check-in Date: **(Check-in Date)**
• Check-out Date: **(Check-out Date)**
• Number of Guests: **(Number of Guests)**
• Total Amount: **(For unpaid bookings only)**
• Booking Platform: **(Booking Platform)**

If you have any special requests or need any assistance before your arrival, please feel free to contact us anytime.

Warm regards,
**(Property Name)**"""


def _template_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    configured = os.getenv("HOTEL_TEMPLATE_DIR", "./hotel_templates")
    path = Path(configured)
    if not path.is_absolute():
        path = root / path
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _safe_hotel_code(hotel_code: str) -> str:
    code = hotel_code.strip().upper()
    if not code or not all(char.isalnum() or char in {"-", "_"} for char in code):
        raise HTTPException(status_code=400, detail="invalid_hotel_code")
    return code


def _template_path(hotel_code: str) -> Path:
    return _template_dir() / f"{_safe_hotel_code(hotel_code)}.json"


def _read_template(hotel_code: str) -> dict[str, Any]:
    path = _template_path(hotel_code)
    if not path.exists():
        raise HTTPException(status_code=404, detail="template_not_found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="template_json_invalid") from exc


def _write_template(*, hotel_code: str, property_name: str, language: str, template: str) -> None:
    code = _safe_hotel_code(hotel_code)
    payload = {
        "hotel_code": code,
        "property_name": property_name.strip(),
        "language": language.strip() or "en",
        "template": template,
    }
    _template_path(code).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; background: #f6f3ea; color: #24211c; }}
    main {{ max-width: 1080px; margin: 32px auto; padding: 24px; }}
    .card {{ background: #fffdf7; border: 1px solid #e2d7be; border-radius: 18px; box-shadow: 0 16px 40px rgba(76, 54, 24, .10); padding: 22px; margin-bottom: 18px; }}
    h1 {{ margin: 0 0 18px; font-size: 28px; }}
    h2 {{ margin: 0 0 12px; font-size: 20px; }}
    label {{ display: block; font-weight: 700; margin: 16px 0 8px; }}
    input, textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #cdbf9e; border-radius: 12px; padding: 12px; font: inherit; background: #fff; }}
    textarea {{ min-height: 560px; line-height: 1.45; white-space: pre-wrap; }}
    button, .button {{ display: inline-block; margin-top: 12px; border: 0; border-radius: 999px; background: #1f6b4f; color: white; padding: 10px 16px; font-weight: 800; cursor: pointer; text-decoration: none; }}
    a {{ color: #1f6b4f; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; border-bottom: 1px solid #e7ddc7; padding: 12px 8px; vertical-align: top; }}
    .row {{ display: grid; grid-template-columns: 1fr 180px; gap: 16px; }}
    .create-row {{ display: grid; grid-template-columns: 160px 1fr 120px; gap: 12px; align-items: end; }}
    .hint {{ color: #776b58; font-size: 14px; margin-top: 10px; }}
    .actions a {{ margin-right: 12px; }}
  </style>
</head>
<body><main>{body}</main></body>
</html>"""


@router.get("/", response_class=HTMLResponse)
def list_hotel_templates() -> str:
    rows = []
    for path in sorted(_template_dir().glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        code = _safe_hotel_code(str(data.get("hotel_code") or path.stem))
        property_name = str(data.get("property_name") or "")
        language = str(data.get("language") or "en")
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(code)}</strong></td>"
            f"<td>{html.escape(property_name)}</td>"
            f"<td>{html.escape(language)}</td>"
            f"<td class=\"actions\"><a href=\"/hotel-templates/{html.escape(code)}/edit\">Edit</a>"
            f"<a href=\"/hotel-templates/{html.escape(code)}.json\">JSON</a></td>"
            "</tr>"
        )
    table_rows = "\n".join(rows) or "<tr><td colspan=\"4\">No templates yet.</td></tr>"
    body = f"""
    <section class="card">
      <h1>Hotel Templates</h1>
      <div class="hint">Create/edit templates here. Each hotel code automatically has a JSON link like <code>/hotel-templates/DN2.json</code>.</div>
    </section>
    <section class="card">
      <h2>Add New Template</h2>
      <form method="post" action="/hotel-templates/">
        <div class="create-row">
          <div>
            <label>Hotel Code</label>
            <input name="hotel_code" placeholder="DN2" required />
          </div>
          <div>
            <label>Property Name</label>
            <input name="property_name" placeholder="Ania Villa" required />
          </div>
          <button type="submit">Create</button>
        </div>
      </form>
    </section>
    <section class="card">
      <h2>Existing Templates</h2>
      <table>
        <thead><tr><th>Code</th><th>Property</th><th>Language</th><th>Links</th></tr></thead>
        <tbody>{table_rows}</tbody>
      </table>
    </section>
    """
    return _page_shell("Hotel Templates", body)


@router.post("/", response_class=HTMLResponse)
def create_hotel_template(
    hotel_code: str = Form(...),
    property_name: str = Form(...),
    language: str = Form("en"),
) -> str:
    code = _safe_hotel_code(hotel_code)
    if _template_path(code).exists():
        raise HTTPException(status_code=409, detail="template_already_exists")
    _write_template(
        hotel_code=code,
        property_name=property_name,
        language=language,
        template=DEFAULT_TEMPLATE.replace("(Property Name)", property_name.strip() or "(Property Name)"),
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8" /><meta http-equiv="refresh" content="0; url=/hotel-templates/{html.escape(code)}/edit" />
<title>Created</title></head><body>Created.</body></html>"""


@router.get("/{hotel_code}.json")
def get_hotel_template(hotel_code: str) -> dict[str, Any]:
    return _read_template(hotel_code)


@router.get("/{hotel_code}/edit", response_class=HTMLResponse)
def edit_hotel_template(hotel_code: str) -> str:
    data = _read_template(hotel_code)
    code = _safe_hotel_code(hotel_code)
    property_name = str(data.get("property_name") or "")
    language = str(data.get("language") or "en")
    template = str(data.get("template") or "")
    body = f"""
    <form class="card" method="post">
      <h1>Edit Hotel Template: {html.escape(code)}</h1>
      <div class="hint"><a href="/hotel-templates/">Back to all templates</a></div>
      <div class="row">
        <div>
          <label>Property Name</label>
          <input name="property_name" value="{html.escape(property_name)}" />
        </div>
        <div>
          <label>Language</label>
          <input name="language" value="{html.escape(language)}" />
        </div>
      </div>
      <label>Template Text</label>
      <textarea name="template">{html.escape(template)}</textarea>
      <button type="submit">Save Template</button>
      <div class="hint">JSON link: <a href="/hotel-templates/{html.escape(code)}.json">/hotel-templates/{html.escape(code)}.json</a></div>
    </form>
    """
    return _page_shell(f"Edit {code} Template", body)


@router.post("/{hotel_code}/edit", response_class=HTMLResponse)
def save_hotel_template(
    hotel_code: str,
    property_name: str = Form(...),
    language: str = Form("en"),
    template: str = Form(...),
) -> str:
    code = _safe_hotel_code(hotel_code)
    _write_template(hotel_code=code, property_name=property_name, language=language, template=template)
    return f"""<!doctype html>
<html><head><meta charset="utf-8" /><meta http-equiv="refresh" content="1; url=/hotel-templates/{html.escape(code)}/edit" />
<title>Saved</title></head><body style="font-family: sans-serif; padding: 32px;">Saved. Returning to editor...</body></html>"""
